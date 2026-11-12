"""Unit test (không cần Ollama/Neo4j) cho ngưỡng RAG và xử lý lệch mô hình/số chiều embedding."""
import logging
import pytest
from backend.app import rag


def row(score, url='u1', **extra):
    return {'id': url, 'title': 'T', 'url': url, 'text': 'x', 'topic': 'Chủ đề', 'review_status': None, 'score': score, **extra}


def test_default_threshold_matches_evaluation():
    assert rag.DEFAULT_THRESHOLD == 0.50


def test_threshold_from_env_parsing(caplog):
    assert rag._threshold_from_env(None) == 0.50
    assert rag._threshold_from_env('') == 0.50
    assert rag._threshold_from_env('0.62') == 0.62
    assert rag._threshold_from_env('0') == 0.0 and rag._threshold_from_env('1') == 1.0
    with caplog.at_level(logging.WARNING):
        for bad in ('abc', '1.5', '-0.1', 'nan'):
            assert rag._threshold_from_env(bad) == 0.50
    assert 'invalid' in caplog.text


def test_threshold_boundary_is_inclusive():
    rows = [row(0.5, 'a'), row(0.4999, 'b'), row(0.8, 'c')]
    got = rag.select_results('hỏi gì đó', rows, top_k=5, threshold=0.50)
    assert [r['url'] for r in got] == ['c', 'a']


def test_none_score_dedupe_and_top_k():
    rows = [row(None, 'n'), row(0.9, 'a'), row(0.8, 'a'), row(0.7, 'b'), row(0.6, 'c')]
    got = rag.select_results('hỏi', rows, top_k=2, threshold=0.5)
    assert [r['url'] for r in got] == ['a', 'b']


def test_out_of_domain_scores_below_default_are_dropped():
    # điểm cao nhất ngoài miền của bge-m3 trong docs/EMBEDDING_EVAL.md là 0.439
    assert rag.select_results('phở bò', [row(0.439)], 3, rag.DEFAULT_THRESHOLD) == []


DOC = {'title': 'WHO: Các loại đái tháo đường và phòng ngừa típ 2', 'topic': 'Các loại tiểu đường và cách phòng ngừa'}
Q = 'Có những loại tiểu đường nào và cách phòng tránh?'


def test_topic_boost_applies_within_margin_below_threshold():
    t = 0.50
    just_inside = t - rag.TOPIC_BOOST_MARGIN
    assert [r['url'] for r in rag.select_results(Q, [row(just_inside, **DOC)], 3, t)] == ['u1']
    assert rag.select_results(Q, [row(just_inside - 0.001, **DOC)], 3, t) == []
    # cùng điểm nhưng câu hỏi không khớp chủ đề thì không được cộng
    assert rag.select_results('Cách nấu phở bò?', [row(just_inside, **DOC)], 3, t) == []


class FakeDB:
    def __init__(self, rows, embedded=0):
        self.rows, self.embedded, self.calls = rows, embedded, []

    def __enter__(self): return self
    def __exit__(self, *a): return False

    def execute_query(self, query, **params):
        self.calls.append((query, params))
        data = self.rows if 'cosine' in query else [{'n': self.embedded}]
        return type('R', (), {'records': data})()


@pytest.fixture
def fake(monkeypatch):
    db = FakeDB([row(0.7, 'a'), row(0.3, 'b')])
    monkeypatch.setattr(rag, 'embed', lambda text: [0.1] * 1024)
    monkeypatch.setattr(rag, 'english_search_query', lambda q: q)
    monkeypatch.setattr(rag, 'driver', lambda: db)
    return db


def test_retrieve_queries_only_current_model_and_dimension(fake):
    got = rag.retrieve('HbA1c là gì?')
    query, params = fake.calls[0]
    assert 'embedding_model = $model' in query and 'size(d.embedding) = $dim' in query
    assert '2 * vector.similarity.cosine' in query  # Neo4j trả (1+cos)/2 -> quy về cosine thuần
    assert params['model'] == rag.EMBED and params['dim'] == 1024
    assert [r['url'] for r in got] == ['a']  # 0.3 < ngưỡng mặc định


def test_retrieve_uses_env_threshold_default_and_explicit_override(fake, monkeypatch):
    monkeypatch.setattr(rag, 'RAG_THRESHOLD', 0.2)
    assert len(rag.retrieve('q')) == 2
    assert len(rag.retrieve('q', threshold=0.9)) == 0


def test_retrieve_warns_when_only_stale_embeddings_exist(monkeypatch, caplog):
    db = FakeDB([], embedded=236)
    monkeypatch.setattr(rag, 'embed', lambda text: [0.1] * 1024)
    monkeypatch.setattr(rag, 'english_search_query', lambda q: q)
    monkeypatch.setattr(rag, 'driver', lambda: db)
    with caplog.at_level(logging.WARNING):
        assert rag.retrieve('q') == []
    assert 're-run ml.seed_knowledge' in caplog.text
