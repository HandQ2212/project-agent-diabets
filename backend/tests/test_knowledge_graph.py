"""Kiểm thử Knowledge Graph Agent và dữ liệu đồ thị/KB, không cần Neo4j thật."""
import json
from pathlib import Path

import pytest

from backend.app import knowledge_graph as kg
from ml.seed_graph import load_graph

ROOT = Path(__file__).resolve().parents[2]
GRAPH = ROOT / 'knowledge/graph_entities.json'
SOURCES = (str(ROOT / 'knowledge/sources.json'), str(ROOT / 'knowledge/sources_v2.json'))


@pytest.fixture(scope='module')
def graph():
    return load_graph(str(GRAPH), SOURCES)


class FakeDB:
    """Mô phỏng execute_query của Neo4j trên dữ liệu JSON."""

    def __init__(self, entities, relations):
        self.entities = {e['id']: e for e in entities}
        self.relations = relations
        self.docs = {d['id']: d for f in SOURCES for d in json.loads(Path(f).read_text(encoding='utf-8'))}

    def execute_query(self, query, **params):
        if query == kg.DOCUMENT_QUERY:
            return [self.docs[i] for i in params['doc_ids'] if i in self.docs], None, None
        if query == kg.ENTITY_QUERY:
            rows = [{'id': e['id'], 'name': e['name'], 'aliases': e.get('aliases', []), 'kind': e['label']}
                    for e in self.entities.values()]
        else:
            ids = set(params['ids'])
            rows = [{'from_id': r['from'], 'from_name': self.entities[r['from']]['name'], 'type': r['type'],
                     'to_id': r['to'], 'to_name': self.entities[r['to']]['name'], 'threshold': r.get('threshold'),
                     'note': r.get('note'), 'source_id': r['source'], 'source_url': r['source_url']}
                    for r in self.relations if r['from'] in ids or r['to'] in ids]
        return rows, None, None


def test_graph_file_is_consistent(graph):
    entities, relations = graph
    assert len(entities) >= 40 and len(relations) >= 50
    assert all(r['source_url'].startswith('https://') for r in relations)


def test_kb_v2_documents_have_required_fields_and_unique_ids():
    docs = [d for f in SOURCES for d in json.loads(Path(f).read_text(encoding='utf-8'))]
    ids = [d['id'] for d in docs]
    assert len(ids) == len(set(ids))
    for d in docs:
        assert {'id', 'title', 'url', 'topic', 'text'} <= d.keys()
        assert d['url'].startswith('https://') and len(d['text']) > 150


def test_match_prefers_specific_entity_and_ignores_generic(graph):
    entities, _ = graph
    matched = kg.match_entities('HbA1c bao nhiêu thì bị tiểu đường?', entities)
    assert [e['id'] for e in matched] == ['hba1c']


def test_match_keeps_accents_so_tim_hieu_is_not_heart(graph):
    entities, _ = graph
    assert kg.match_entities('Tôi muốn tìm hiểu về tiểu đường', entities) == []
    assert 'tim-mach' in [e['id'] for e in kg.match_entities('Tiểu đường có hại tim không?', entities)]


def test_match_requires_whole_word(graph):
    entities, _ = graph
    # 'mắt' không được khớp bên trong từ khác
    assert 'bien-chung-mat' not in [e['id'] for e in kg.match_entities('mắtxích', entities)]


def test_lookup_returns_threshold_facts_with_citation(graph):
    entities, relations = graph
    source = kg.lookup('HbA1c là gì?', FakeDB(entities, relations))
    assert source['review_status'] == kg.GRAPH_REVIEW_STATUS
    assert '≥ 6,5%' in source['text'] and '5,7–6,4%' in source['text']
    assert source['url'].startswith('https://www.niddk.nih.gov/')
    assert len(source['facts']) <= kg.MAX_FACTS


def test_lookup_ranks_relation_between_two_asked_entities_first(graph):
    entities, relations = graph
    source = kg.lookup('Béo bụng có làm tăng nguy cơ tiểu đường típ 2 không?', FakeDB(entities, relations))
    first = source['facts'][0]
    assert (first['from_id'], first['type'], first['to_id']) == ('beo-bung', 'INCREASES_RISK_OF', 'dtd-typ2')


def test_lookup_returns_none_without_entity_and_survives_db_errors(graph):
    entities, relations = graph
    assert kg.lookup('Xin chào', FakeDB(entities, relations)) is None

    class Broken:
        def execute_query(self, *a, **k):
            raise ConnectionError('neo4j down')
    assert kg.lookup('HbA1c là gì?', Broken()) is None


def test_format_fact_reads_naturally():
    fact = {'from_name': 'HbA1c', 'type': 'DIAGNOSES', 'to_name': 'Đái tháo đường', 'threshold': '≥ 6,5%', 'note': None}
    assert kg.format_fact(fact) == 'HbA1c dùng để chẩn đoán Đái tháo đường (ngưỡng: ≥ 6,5%).'


def test_chat_appends_graph_source_and_trace(monkeypatch):
    from fastapi.testclient import TestClient
    from backend.app import main
    graph_source = {'title': 'Đồ thị tri thức Neo4j: HbA1c', 'url': 'https://www.niddk.nih.gov/', 'topic': 'Đồ thị tri thức',
                    'text': 'HbA1c dùng để chẩn đoán Đái tháo đường.', 'review_status': 'curated_graph', 'facts': [{}]}
    monkeypatch.setattr(main.rag, 'standalone_question', lambda q, h: q)
    # Cổng DEF-BE-3: đồ thị chỉ được tra khi RAG có ≥1 nguồn.
    rag_source = {'title': 'HbA1c', 'url': 'https://example.org/hba1c', 'text': 'x', 'topic': 'Xét nghiệm'}
    monkeypatch.setattr(main.rag, 'retrieve', lambda *a, **k: [rag_source])
    monkeypatch.setattr(main.knowledge_graph, 'lookup', lambda q: graph_source)
    seen = {}
    monkeypatch.setattr(main.rag, 'answer', lambda q, sources, history: seen.update(sources=sources) or 'HbA1c [1].')
    response = TestClient(main.app).post('/api/chat', json={'question': 'HbA1c là gì?'})
    body = response.json()
    assert response.status_code == 200
    assert seen['sources'] == [rag_source, graph_source]
    assert body['sources'][1]['review_status'] == 'curated_graph'
    assert 'Knowledge Graph Agent (1 facts, +0 linked docs)' in body['trace']


def test_lookup_attaches_cited_documents_for_detail(graph):
    """Câu hỏi hạ đường huyết phải kéo theo đoạn gốc có quy tắc 15–15 chi tiết (tránh LLM tự bịa lượng đường)."""
    entities, relations = graph
    source = kg.lookup('Bị hạ đường huyết thì xử trí thế nào?', FakeDB(entities, relations))
    doc_ids = [d['id'] for d in source['documents']]
    assert 'kb2-ha-duong-huyet-15-15' in doc_ids
    assert len(doc_ids) <= kg.MAX_LINKED_DOCUMENTS


def test_merge_sources_skips_documents_already_retrieved():
    doc = {'title': 'A', 'url': 'https://a', 'text': 'x'}
    other = {'title': 'B', 'url': 'https://b', 'text': 'y'}
    graph_source = {'title': 'Đồ thị', 'url': 'https://a', 'text': 'f', 'facts': [{}], 'documents': [doc, other]}
    merged = kg.merge_sources([doc], graph_source)
    assert [m['title'] for m in merged] == ['A', 'B', 'Đồ thị']
    assert 'documents' not in merged[-1]
    assert kg.merge_sources([doc], None) == [doc]
