"""REQ-DA-04 B-1/B-2/B-3 (design-ui.md 6b): review_status curated, publisher, facts[] cho nguồn của /api/chat(/stream)."""
import json
import logging
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app import main, publishers

ROOT = Path(__file__).resolve().parents[2]


# --- B-2: publisher theo id ----------------------------------------------------------------------------

def test_every_shipped_source_has_a_publisher_and_ids_are_unique():
    entries = [e for f in publishers.SOURCE_FILES for e in json.loads((ROOT / 'knowledge' / f).read_text(encoding='utf-8'))]
    mapping = publishers.load_publishers(ROOT / 'knowledge')
    assert len(mapping) == len(entries)
    assert {'ADA', 'Bộ Y tế', 'WHO', 'CDC', 'NIDDK'} <= set(mapping.values())


@pytest.mark.parametrize('doc_id,publisher', [
    ('kb2-muc-tieu-kiem-soat', 'ADA'), ('kb2-muc-tieu-bytvn', 'Bộ Y tế'), ('who-diabetes-overview', 'WHO'),
    ('cdc-classic-symptoms', 'CDC'), ('kb2-hba1c-la-gi', 'NIDDK'),
    ('cdc-prevention-lifestyle', 'NIDDK'),          # id "cdc-" nhưng nội dung là NIDDK: gán theo nguồn thật
])
def test_publishers_follow_the_source_not_the_id_prefix(doc_id, publisher):
    assert publishers.load_publishers(ROOT / 'knowledge')[doc_id] == publisher


@pytest.mark.parametrize('entries', [[{'id': 'a'}], [{'id': 'a', 'publisher': '  '}],
                                     [{'id': 'a', 'publisher': 'ADA'}, {'id': 'a', 'publisher': 'WHO'}]])
def test_parse_publishers_fails_fast_on_bad_data(entries):
    with pytest.raises(ValueError):
        publishers.parse_publishers(entries)


def test_registry_degrades_to_none_when_files_are_broken(caplog):
    def broken():
        raise FileNotFoundError('knowledge/sources.json')
    registry = publishers.PublisherRegistry(broken)
    with caplog.at_level(logging.WARNING):
        assert registry.get('kb2-muc-tieu-bytvn') is None
    assert 'publisher will be null' in caplog.text
    assert registry.get(None) is None


# --- B-1, B-2, B-3: source_summary --------------------------------------------------------------------

FACT = {'from_id': 'hba1c', 'from_name': 'HbA1c', 'type': 'DIAGNOSES', 'to_id': 'dtd', 'to_name': 'Đái tháo đường',
        'threshold': '≥ 6,5%', 'note': None, 'source_id': 'kb2-tieu-chuan-chan-doan-so', 'source_url': 'https://x'}
CURATED_DOC = {'id': 'kb2-muc-tieu-bytvn', 'title': 'Mục tiêu (Bộ Y tế)', 'url': 'https://byt', 'text': 't',
               'topic': 'Mục tiêu', 'review_status': None, 'fetched_at': None, 'score': 0.7}
WEB_DOC = {'id': 'web:cdc:1', 'title': 'CDC page', 'url': 'https://www.cdc.gov/x', 'text': 't', 'topic': 'Web',
           'review_status': 'unreviewed_web', 'fetched_at': '2026-11-12T10:00:00+07:00'}
GRAPH = {'title': 'Đồ thị tri thức Neo4j: HbA1c', 'url': 'https://x', 'topic': 'Đồ thị tri thức', 'text': 't',
         'review_status': 'curated_graph',
         'facts': [FACT, dict(FACT, type='MONITORED_BY', to_name='Bệnh thận', threshold=None), {}]}


def test_b1_curated_document_is_marked_curated_with_publisher():
    assert main.source_summary(CURATED_DOC) == {
        'title': 'Mục tiêu (Bộ Y tế)', 'url': 'https://byt', 'topic': 'Mục tiêu', 'review_status': 'curated',
        'fetched_at': None, 'publisher': 'Bộ Y tế'}


def test_b1_web_source_keeps_status_and_has_no_publisher():
    summary = main.source_summary(WEB_DOC)
    assert summary['review_status'] == 'unreviewed_web' and summary['publisher'] is None
    assert 'facts' not in summary and 'text' not in summary and 'id' not in summary


def test_b2_unknown_curated_id_has_null_publisher():
    assert main.source_summary(dict(CURATED_DOC, id='who-diabetes'))['publisher'] is None


def test_b3_graph_source_returns_facts_and_skips_incomplete_ones():
    summary = main.source_summary(GRAPH)
    assert summary['review_status'] == 'curated_graph' and summary['publisher'] is None
    assert summary['facts'] == [
        {'from': 'HbA1c', 'type': 'DIAGNOSES', 'to': 'Đái tháo đường', 'threshold': '≥ 6,5%'},
        {'from': 'HbA1c', 'type': 'MONITORED_BY', 'to': 'Bệnh thận'}]


@pytest.fixture
def chat_pipeline(monkeypatch):
    monkeypatch.setattr(main.rag, 'standalone_question', lambda q, h: q)
    monkeypatch.setattr(main.rag, 'retrieve', lambda *a, **k: [dict(CURATED_DOC), dict(WEB_DOC)])
    monkeypatch.setattr(main.knowledge_graph, 'lookup', lambda *a, **k: dict(GRAPH))
    monkeypatch.setattr(main.history, 'record', lambda kind: None)


def test_chat_endpoint_returns_b1_b2_b3_fields(chat_pipeline, monkeypatch):
    monkeypatch.setattr(main.rag, 'answer', lambda q, sources, history: 'Trả lời [1].')
    body = TestClient(main.app).post('/api/chat', json={'question': 'Mục tiêu HbA1c?'}).json()
    statuses = [s['review_status'] for s in body['sources']]
    assert statuses == ['curated', 'unreviewed_web', 'curated_graph']
    assert body['sources'][0]['publisher'] == 'Bộ Y tế'
    assert body['sources'][2]['facts'][0] == {'from': 'HbA1c', 'type': 'DIAGNOSES', 'to': 'Đái tháo đường',
                                              'threshold': '≥ 6,5%'}


def test_stream_done_event_returns_the_same_sources(chat_pipeline, monkeypatch):
    monkeypatch.setattr(main.rag, 'answer_parts', lambda *a, **k: iter(['Trả lời [1].']))
    lines = TestClient(main.app).post('/api/chat/stream', json={'question': 'Mục tiêu HbA1c?'}).text.splitlines()
    done = json.loads(lines[-1])
    assert done['type'] == 'done'
    assert done['sources'] == [main.source_summary(CURATED_DOC), main.source_summary(WEB_DOC), main.source_summary(GRAPH)]


def test_summary_tolerates_missing_title_and_url():
    summary = main.source_summary({'id': 'x', 'text': 't'})
    assert summary['title'] is None and summary['url'] is None and summary['review_status'] == 'curated'
