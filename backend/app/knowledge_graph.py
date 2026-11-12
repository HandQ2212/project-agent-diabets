"""Knowledge Graph Agent: tra cứu quan hệ có cấu trúc trong Neo4j.

Khác với RAG (tìm đoạn văn gần nghĩa bằng vector), agent này nhận diện thực thể y khoa
trong câu hỏi (bệnh, triệu chứng, yếu tố nguy cơ, xét nghiệm, biến chứng, phòng ngừa)
rồi lấy các bộ ba (thực thể)-[quan hệ]->(thực thể) kèm ngưỡng và nguồn trích dẫn.
Kết quả được đóng gói thành một "nguồn" để Response Agent dùng cùng các đoạn RAG.

Phần nhận diện thực thể và định dạng là hàm thuần, kiểm thử được không cần Neo4j.
"""
import logging
import re
import unicodedata
from typing import Iterable

log = logging.getLogger(__name__)

# Diễn đạt tiếng Việt của từng loại quan hệ (chiều from -> to).
RELATION_TEXT = {
    'IS_A': 'là một thể của',
    'PROGRESSES_TO': 'có thể tiến triển thành',
    'HAS_SYMPTOM': 'có triệu chứng',
    'INCREASES_RISK_OF': 'làm tăng nguy cơ',
    'CAUSES': 'là cơ chế gây ra',
    'DIAGNOSES': 'dùng để chẩn đoán',
    'CAN_CAUSE': 'có thể gây biến chứng',
    'MONITORED_BY': 'được theo dõi bằng',
    'REDUCES_RISK_OF': 'giúp giảm nguy cơ',
    'TREATS': 'dùng để xử trí',
}
# Thực thể quá chung (gần như câu nào cũng nhắc) không tự kích hoạt tra cứu đồ thị.
GENERIC_ENTITIES = {'dtd'}
MAX_FACTS = 10
GRAPH_REVIEW_STATUS = 'curated_graph'


def _normalize(text: str) -> str:
    """Chữ thường, chuẩn Unicode NFC, gộp khoảng trắng. Giữ dấu để 'tìm' không khớp 'tim'."""
    text = unicodedata.normalize('NFC', text.lower())
    return ' '.join(re.sub(r'[^\w\s%-]', ' ', text).split())


def match_entities(question: str, entities: Iterable[dict]) -> list[dict]:
    """Trả về các thực thể có tên/alias xuất hiện trọn từ trong câu hỏi.

    Ưu tiên alias dài hơn (cụ thể hơn); bỏ thực thể chung nếu đã có thực thể cụ thể.
    """
    q = f' {_normalize(question)} '
    found: dict[str, tuple[int, dict]] = {}
    for entity in entities:
        names = [entity.get('name', ''), *entity.get('aliases', [])]
        best = 0
        for name in names:
            alias = _normalize(name)
            if alias and re.search(rf'(?<!\w){re.escape(alias)}(?!\w)', q):
                best = max(best, len(alias))
        if best:
            found[entity['id']] = (best, entity)
    ranked = [e for _, e in sorted(found.values(), key=lambda pair: -pair[0])]
    specific = [e for e in ranked if e['id'] not in GENERIC_ENTITIES]
    return specific


def format_fact(fact: dict) -> str:
    """Một dòng mô tả bộ ba, ví dụ: 'HbA1c dùng để chẩn đoán Đái tháo đường (ngưỡng: ≥ 6,5%)'."""
    verb = RELATION_TEXT.get(fact['type'], fact['type'].lower())
    line = f"{fact['from_name']} {verb} {fact['to_name']}"
    extras = [f"ngưỡng: {fact['threshold']}" if fact.get('threshold') else '', fact.get('note') or '']
    extras = [e for e in extras if e]
    return line + (f" ({'; '.join(extras)})" if extras else '') + '.'


def facts_to_source(entities: list[dict], facts: list[dict]) -> dict | None:
    """Đóng gói các bộ ba thành một nguồn cho Response Agent; None nếu không có gì."""
    if not facts:
        return None
    facts = facts[:MAX_FACTS]
    urls = []
    for fact in facts:
        if fact.get('source_url') and fact['source_url'] not in urls:
            urls.append(fact['source_url'])
    names = ', '.join(e['name'] for e in entities[:3])
    return {
        'title': f'Đồ thị tri thức Neo4j: {names}',
        'url': urls[0] if urls else '',
        'topic': 'Đồ thị tri thức',
        'text': ' '.join(format_fact(f) for f in facts) + (f" Nguồn gốc các quan hệ: {', '.join(urls)}." if urls else ''),
        'review_status': GRAPH_REVIEW_STATUS,
        'facts': facts,
    }


ENTITY_QUERY = 'MATCH (e:Entity) RETURN e.id AS id, e.name AS name, e.aliases AS aliases, e.kind AS kind'
FACT_QUERY = '''
MATCH (a:Entity)-[r]->(b:Entity)
WHERE a.id IN $ids OR b.id IN $ids
RETURN a.id AS from_id, a.name AS from_name, type(r) AS type, b.id AS to_id, b.name AS to_name,
       r.threshold AS threshold, r.note AS note, r.source_id AS source_id, r.source_url AS source_url
'''


def rank_facts(facts: list[dict], entity_ids: list[str]) -> list[dict]:
    """Ưu tiên quan hệ nối hai thực thể đều được hỏi, rồi theo thứ tự thực thể trong danh sách."""
    order = {eid: i for i, eid in enumerate(entity_ids)}
    def key(f):
        both = f['from_id'] in order and f['to_id'] in order
        first = min(order.get(f['from_id'], 99), order.get(f['to_id'], 99))
        return (0 if both else 1, first, f['type'], f['to_name'])
    return sorted(facts, key=key)


DOCUMENT_QUERY = '''
MATCH (d:Document) WHERE d.id IN $doc_ids
RETURN d.id AS id, d.title AS title, d.url AS url, d.text AS text, d.topic AS topic,
       d.date AS date, d.license AS license, d.review_status AS review_status
'''
MAX_LINKED_DOCUMENTS = 2


def linked_document_ids(facts: list[dict], limit: int = MAX_LINKED_DOCUMENTS) -> list[str]:
    """Id tài liệu gốc được trích dẫn bởi các bộ ba xếp hạng cao nhất (không trùng, giữ thứ tự)."""
    ids: list[str] = []
    for fact in facts[:MAX_FACTS]:
        if fact.get('source_id') and fact['source_id'] not in ids:
            ids.append(fact['source_id'])
        if len(ids) >= limit:
            break
    return ids


def lookup(question: str, db=None) -> dict | None:
    """Tra cứu đồ thị cho câu hỏi. Lỗi Neo4j không chặn luồng chat (trả None).

    Trả về nguồn 'bộ ba' đã đóng gói; khóa 'documents' chứa các đoạn tài liệu gốc mà các
    bộ ba trích dẫn (cạnh DESCRIBED_IN), để Response Agent có đủ chi tiết thay vì tự suy diễn.
    """
    try:
        if db is None:
            from backend.app.rag import driver
            with driver() as conn:
                return lookup(question, conn)
        records, _, _ = db.execute_query(ENTITY_QUERY, database_='neo4j')
        entities = [dict(r) | {'aliases': list(r['aliases'] or [])} for r in records]
        matched = match_entities(question, entities)
        if not matched:
            return None
        ids = [e['id'] for e in matched]
        records, _, _ = db.execute_query(FACT_QUERY, ids=ids, database_='neo4j')
        facts = rank_facts([dict(r) for r in records], ids)
        source = facts_to_source(matched, facts)
        if source is None:
            return None
        doc_ids = linked_document_ids(facts)
        docs, _, _ = db.execute_query(DOCUMENT_QUERY, doc_ids=doc_ids, database_='neo4j') if doc_ids else ([], None, None)
        by_id = {d['id']: dict(d) for d in docs}
        source['documents'] = [by_id[i] for i in doc_ids if i in by_id]
        return source
    except Exception:
        log.warning('Knowledge graph lookup failed; continuing with vector retrieval only', exc_info=True)
        return None


def merge_sources(retrieved: list[dict], graph_source: dict | None) -> list[dict]:
    """Thêm tài liệu do đồ thị dẫn tới (nếu RAG chưa có, so theo URL+tiêu đề) và nguồn bộ ba vào cuối."""
    if not graph_source:
        return retrieved
    seen = {(s.get('url'), s.get('title')) for s in retrieved}
    linked = [d for d in graph_source.get('documents', []) if (d.get('url'), d.get('title')) not in seen]
    facts_only = {k: v for k, v in graph_source.items() if k != 'documents'}
    return retrieved + linked + [facts_only]
