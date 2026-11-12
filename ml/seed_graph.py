"""Nạp đồ thị tri thức (thực thể + quan hệ) từ knowledge/graph_entities.json vào Neo4j.

Chạy sau `python -m ml.seed_knowledge` để quan hệ DESCRIBED_IN nối được tới các Document đã có:
    docker compose exec api python -m ml.seed_graph
Idempotent: dùng MERGE nên chạy lại không tạo trùng.
"""
import json
import logging
from pathlib import Path

from backend.app.rag import driver

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

LABELS = {'Disease', 'Symptom', 'RiskFactor', 'Test', 'Complication', 'Prevention'}
RELATION_TYPES = {'IS_A', 'PROGRESSES_TO', 'HAS_SYMPTOM', 'INCREASES_RISK_OF', 'CAUSES', 'DIAGNOSES',
                  'CAN_CAUSE', 'MONITORED_BY', 'REDUCES_RISK_OF', 'TREATS'}
SOURCE_FILES = ('knowledge/sources.json', 'knowledge/sources_v2.json')


def load_graph(path: str = 'knowledge/graph_entities.json', source_files=SOURCE_FILES) -> tuple[list, list]:
    """Đọc và kiểm tra tính toàn vẹn: nhãn/quan hệ hợp lệ, id tồn tại, nguồn trích dẫn tồn tại."""
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    sources = {doc['id']: doc['url'] for f in source_files if Path(f).exists()
               for doc in json.loads(Path(f).read_text(encoding='utf-8'))}
    entities, relations = data['entities'], data['relations']
    ids = {e['id'] for e in entities}
    if len(ids) != len(entities):
        raise ValueError('Trùng id thực thể')
    for e in entities:
        if e['label'] not in LABELS:
            raise ValueError(f"Nhãn không hợp lệ: {e}")
    for r in relations:
        if r['type'] not in RELATION_TYPES:
            raise ValueError(f'Quan hệ không hợp lệ: {r}')
        if r['from'] not in ids or r['to'] not in ids:
            raise ValueError(f'Quan hệ trỏ tới thực thể không tồn tại: {r}')
        if r['source'] not in sources:
            raise ValueError(f'Nguồn trích dẫn không tồn tại: {r}')
        r['source_url'] = sources[r['source']]
    return entities, relations


def seed(path: str = 'knowledge/graph_entities.json'):
    entities, relations = load_graph(path)
    with driver() as db:
        db.execute_query('CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE', database_='neo4j')
        for e in entities:
            # Nhãn chỉ lấy từ tập LABELS đã kiểm tra nên ghép vào Cypher an toàn.
            db.execute_query(
                f'MERGE (e:Entity {{id: $id}}) SET e:{e["label"]}, e.name = $name, e.aliases = $aliases, e.kind = $kind',
                id=e['id'], name=e['name'], aliases=e.get('aliases', []), kind=e['label'], database_='neo4j')
        for r in relations:
            db.execute_query(
                f'''MATCH (a:Entity {{id: $from_id}}) MATCH (b:Entity {{id: $to_id}})
                    MERGE (a)-[rel:{r["type"]}]->(b)
                    SET rel.threshold = $threshold, rel.note = $note, rel.source_id = $source_id, rel.source_url = $source_url
                    WITH a, b
                    OPTIONAL MATCH (d:Document {{id: $source_id}})
                    FOREACH (_ IN CASE WHEN d IS NULL THEN [] ELSE [1] END |
                        MERGE (a)-[:DESCRIBED_IN]->(d) MERGE (b)-[:DESCRIBED_IN]->(d))''',
                from_id=r['from'], to_id=r['to'], threshold=r.get('threshold'), note=r.get('note'),
                source_id=r['source'], source_url=r['source_url'], database_='neo4j')
    log.info('Loaded %d entities and %d relations into Neo4j', len(entities), len(relations))


if __name__ == '__main__':
    seed()
