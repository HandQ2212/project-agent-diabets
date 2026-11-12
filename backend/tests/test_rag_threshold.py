"""Unit test (không cần Ollama/Neo4j) cho ngưỡng RAG và xử lý lệch mô hình/số chiều embedding."""
import logging
import pytest
from backend.app import rag


def row(score, url='u1', **extra):
    return {'id': url, 'title': 'T', 'url': url, 'text': 'x', 'topic': 'Chủ đề', 'review_status': None, 'score': score, **extra}


def test_default_threshold_matches_evaluation():
    assert rag.DEFAULT_THRESHOLD == 0.53


def test_threshold_from_env_parsing(caplog):
    assert rag._threshold_from_env(None) == 0.53
    assert rag._threshold_from_env('') == 0.53
    assert rag._threshold_from_env('0.62') == 0.62
    assert rag._threshold_from_env('0') == 0.0 and rag._threshold_from_env('1') == 1.0
    with caplog.at_level(logging.WARNING):
        for bad in ('abc', '1.5', '-0.1', 'nan'):
            assert rag._threshold_from_env(bad) == 0.53
    assert 'invalid' in caplog.text


def test_threshold_boundary_is_inclusive():
    rows = [row(0.5, 'a'), row(0.4999, 'b'), row(0.8, 'c')]
    got = rag.select_results('hỏi gì đó', rows, top_k=5, threshold=0.50)
    assert [r['url'] for r in got] == ['c', 'a']


@pytest.mark.parametrize('score,kept', [(0.5299, False), (0.53, True), (0.5301, True)])
def test_default_threshold_boundary_below_at_and_above(score, kept):
    got = rag.select_results('hỏi gì đó', [row(score)], 3, rag.DEFAULT_THRESHOLD)
    assert (got != []) is kept


@pytest.mark.parametrize('score', [0.501, 0.516, 0.522])
def test_measured_out_of_domain_entity_questions_are_dropped_at_default(score):
    # 'Giá vé xem phim tăng huyết áp không?' 0.501 / bản không dấu 0.516 / 'Bóng đá Việt Nam và bệnh tim mạch' 0.522
    assert rag.select_results('câu ngoài miền', [row(score)], 3, rag.DEFAULT_THRESHOLD) == []


def test_lowest_measured_in_domain_score_is_kept_at_default():
    # 'Nhiễm toan ceton và tăng áp lực thẩm thấu là gì?' 0.567
    assert len(rag.select_results('ceton', [row(0.567)], 3, rag.DEFAULT_THRESHOLD)) == 1


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


# --- Ưu tiên curated hơn unreviewed_web có điểm sát nhau (bổ sung vòng 1, câu "Bao nhiêu tuổi thì nên xét nghiệm") ---

def web(score, url, **extra):
    return row(score, url, review_status='unreviewed_web', **extra)


def test_curated_outranks_close_unreviewed_web_rows():
    # điểm thật đo được: web 0.755 / 0.737, curated VN 0.734, curated ADA 0.716
    rows = [web(0.755, 'w1'), web(0.737, 'w2'), row(0.734, 'vn'), row(0.716, 'ada')]
    assert [r['url'] for r in rag.select_results('tuổi xét nghiệm', rows, 3, 0.5)] == ['vn', 'ada', 'w1']


def test_web_row_far_above_curated_keeps_its_rank():
    rows = [web(0.80, 'w'), row(0.70, 'c')]
    assert [r['url'] for r in rag.select_results('q', rows, 3, 0.5)] == ['w', 'c']


def test_curated_priority_does_not_lower_the_threshold():
    rows = [row(0.5 - rag.CURATED_PRIORITY / 2, 'c'), web(0.6, 'w')]
    assert [r['url'] for r in rag.select_results('q', rows, 3, 0.5)] == ['w']
    assert rag.select_results('Cách nấu phở bò?', [row(0.49, 'c')], 3, 0.5) == []


def test_url_dedupe_keeps_curated_row_over_close_web_chunk_of_same_url():
    rows = [web(0.588, 'same', id='web:niddk-a1c:1'), row(0.562, 'same', id='kb2-hba1c-la-gi')]
    assert [r['id'] for r in rag.select_results('hba1c', rows, 3, 0.5)] == ['kb2-hba1c-la-gi']
