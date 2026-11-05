"""Periodically collect allowlisted public health pages into Neo4j.

Only explicitly configured sources are fetched. Web content remains labeled as
unreviewed and must not be treated as medical advice.
"""
import argparse
import hashlib
import json
import logging
import os
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
from backend.app.rag import driver, embed

log = logging.getLogger(__name__)
ALLOWED_HOSTS = {'www.cdc.gov', 'www.niddk.nih.gov'}
MAX_BYTES = 2_000_000
USER_AGENT = 'DuongAnAcademicBot/1.0 (educational project)'

class MainText(HTMLParser):
    """Extract paragraph, list and heading text within the main page content."""
    BLOCKS = {'p', 'li', 'h1', 'h2', 'h3'}
    SKIP = {'script', 'style', 'nav', 'footer', 'header', 'noscript', 'svg'}
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_main = False
        self.skip = 0
        self.current = None
        self.parts = []
        self.blocks = []
    def handle_starttag(self, tag, attrs):
        if tag == 'main': self.in_main = True
        if not self.in_main: return
        if tag in self.SKIP: self.skip += 1
        if not self.skip and tag in self.BLOCKS and self.current is None:
            self.current = tag; self.parts = []
    def handle_data(self, data):
        if self.in_main and not self.skip and self.current:
            self.parts.append(data)
    def handle_endtag(self, tag):
        if tag in self.SKIP and self.skip:
            self.skip -= 1
        if not self.skip and tag == self.current:
            text = ' '.join(' '.join(self.parts).split())
            if len(text) >= 25: self.blocks.append(text)
            self.current = None; self.parts = []
        if tag == 'main': self.in_main = False

def valid_url(url):
    parsed = urlparse(url)
    return parsed.scheme == 'https' and parsed.hostname in ALLOWED_HOSTS and not parsed.username and not parsed.password and parsed.port in (None, 443)

def fetch(client, url):
    for _ in range(4):
        if not valid_url(url): raise ValueError('URL outside allowed health sources')
        with client.stream('GET', url, follow_redirects=False) as response:
            if response.status_code in (301, 302, 303, 307, 308):
                url = urljoin(url, response.headers['location']); continue
            response.raise_for_status()
            if 'text/html' not in response.headers.get('content-type', '').lower(): raise ValueError('Not an HTML page')
            body = bytearray()
            for part in response.iter_bytes():
                body.extend(part)
                if len(body) > MAX_BYTES: raise ValueError('Page exceeds size limit')
            return bytes(body).decode(response.encoding or 'utf-8', errors='replace'), str(response.url)
    raise ValueError('Too many redirects')

def robots_allowed(client, url):
    parsed = urlparse(url)
    robots_url = f'{parsed.scheme}://{parsed.netloc}/robots.txt'
    response = client.get(robots_url, follow_redirects=False)
    if response.status_code in (401, 403): return False
    if response.status_code == 404: return True
    response.raise_for_status()
    parser = RobotFileParser(); parser.parse(response.text.splitlines())
    return parser.can_fetch(USER_AGENT, url)

def make_chunks(blocks, limit=1200):
    chunks, current = [], ''
    for block in blocks:
        # Bound long blocks as well as combined chunks.
        for start in range(0, len(block), limit):
            part = block[start:start+limit]
            if current and len(current) + len(part) + 1 > limit:
                chunks.append(current); current = ''
            current = f'{current}\n{part}'.strip()
    if current: chunks.append(current)
    return chunks

def refresh_source(db, client, source):
    url = source['url']
    if not valid_url(url) or not robots_allowed(client, url): raise ValueError('URL is disallowed by source policy or robots.txt')
    html, final_url = fetch(client, url)
    if final_url != url and not robots_allowed(client, final_url): raise ValueError('Redirect destination disallowed by robots.txt')
    parser = MainText(); parser.feed(html)
    chunks = make_chunks(parser.blocks)
    if not chunks: raise ValueError('Could not extract main content')
    digest = hashlib.sha256('\n'.join(chunks).encode()).hexdigest()
    existing = db.execute_query('MATCH (s:WebSource {id:$id}) RETURN s.content_hash AS digest', id=source['id'], database_='neo4j').records
    fetched_at = datetime.now(timezone.utc).isoformat()
    if existing and existing[0]['digest'] == digest:
        db.execute_query('MATCH (s:WebSource {id:$id}) SET s.fetched_at=$fetched_at', id=source['id'], fetched_at=fetched_at, database_='neo4j')
        return 0
    # Complete all embeddings before touching existing chunks; a download or model failure retains the prior version.
    records = [{'id': f"web:{source['id']}:{i}", 'text': text, 'embedding': embed(text)} for i, text in enumerate(chunks)]
    def write(tx):
        tx.run('MERGE (s:WebSource {id:$id}) SET s.url=$url, s.content_hash=$digest, s.fetched_at=$fetched_at', id=source['id'], url=final_url, digest=digest, fetched_at=fetched_at).consume()
        tx.run('MATCH (d:Document {web_source_id:$id}) DETACH DELETE d', id=source['id']).consume()
        tx.run('''MATCH (s:WebSource {id:$source_id}) MERGE (t:Topic {name:$topic})
                  WITH s,t UNWIND $records AS row
                  CREATE (d:Document {id:row.id, text:row.text, embedding:row.embedding,
                     web_source_id:$source_id, title:$title, url:$url, topic:$topic,
                     fetched_at:$fetched_at, review_status:'unreviewed_web'})
                  CREATE (d)-[:ABOUT]->(t) CREATE (d)-[:FROM_SOURCE]->(s)''',
               source_id=source['id'], topic=source['topic'], title=f"{source['topic']} — nguồn web tự động", url=final_url, fetched_at=fetched_at, records=records).consume()
    with db.session(database='neo4j') as session: session.execute_write(write)
    return len(records)

def refresh(path='knowledge/web_sources.json'):
    sources = json.loads(Path(path).read_text(encoding='utf-8'))
    failures = 0
    with driver() as db, httpx.Client(timeout=30, headers={'User-Agent': USER_AGENT}) as client:
        for source in sources:
            try:
                count = refresh_source(db, client, source)
                log.info('Source %s refreshed (%d new chunks)', source['id'], count)
            except Exception:
                failures += 1
                log.exception('Source %s failed; existing knowledge retained', source.get('id', 'unknown'))
    return failures

def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--loop', action='store_true'); parser.add_argument('--sources', default='knowledge/web_sources.json')
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    while True:
        try: failures = refresh(args.sources)
        except Exception:
            log.exception('Knowledge refresh failed')
            failures = 1
        if not args.loop:
            if failures: raise SystemExit(1)
            break
        time.sleep(900 if failures else max(3600, int(os.getenv('KNOWLEDGE_REFRESH_SECONDS', '86400'))))

if __name__ == '__main__': main()
