import json
from pathlib import Path
from backend.app.rag import driver, embed

if __name__ == '__main__':
    docs = json.loads(Path('knowledge/sources.json').read_text())
    with driver() as db:
        db.execute_query('CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE', database_='neo4j')
        for doc in docs:
            vector = embed(doc['text'])
            db.execute_query('MERGE (d:Document {id: $id}) SET d.title=$title, d.url=$url, d.text=$text, d.embedding=$embedding MERGE (t:Topic {name: $topic}) MERGE (d)-[:ABOUT]->(t)', **doc, embedding=vector, database_='neo4j')
    print(f'Loaded {len(docs)} documents')
