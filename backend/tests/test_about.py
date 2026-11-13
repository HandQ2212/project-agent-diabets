"""REQ-DA-04: GET /api/about (design-ui.md 6c)."""
import json
import logging
import math
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app import about, main, publishers

ROOT = Path(__file__).resolve().parents[2]


# --- /api/about: đọc report -------------------------------------------------------------------------------

MLP_REPORT = {
    'train': 160, 'validation': 40, 'test': 51, 'test_positive_fraction': 0.6862745098039216,
    'neural_network': {'confusion_matrix': [[16, 0], [10, 25]], 'roc_auc': 0.9232142857142858,
                       'brier_score': 0.13271072506904602,
                       'classification_report': {'1': {'precision': 1.0, 'recall': 0.7142857142857143,
                                                       'f1-score': 0.8333333333333334}, 'accuracy': 0.803921568627451}},
    'logistic_regression': {'roc_auc': 0.9125, 'classification_report': {'1': {'f1-score': 0.8571428571428571}}},
}
NHANES4_REPORT = {
    'train_n': 1988, 'validation_n': 497, 'test_cycle': {'complete': 2408},
    'cnn': {'roc_auc': 0.9489937932607262, 'accuracy': 0.8866279069767442, 'precision': 0.611864406779661,
            'recall': 0.891358024691358, 'f1': 0.7256281407035176, 'confusion_matrix': [[1774, 229], [44, 361]]},
    'logistic_regression': {'roc_auc': 0.9418810056520158, 'f1': 0.7300930713547052},
}
NHANES15_REPORT = {
    'sizes': {'train': 1680, 'validation': 414, 'test': 2038}, 'selected_threshold': 0.8,
    'selection_rule': 'highest validation ROC-AUC; ties favor baseline order; threshold max F1 on validation',
    'validation_metrics': {'logistic_regression': {'roc_auc': 0.9499303378613724, 'f1': 0.6703910614525139}},
    'test_selected_only': {'roc_auc': 0.9313555986618313, 'precision': 0.7583081570996979, 'recall': 0.7514970059880239,
                           'f1': 0.7548872180451128, 'accuracy': 0.9200196270853778, 'brier': 0.09163831919431686,
                           'confusion_matrix': [[1624, 80], [83, 251]]},
    'test_auc_bootstrap_stratified_95': [0.9129948290039639, 0.9487296533693177],
}
RL_REPORT = {'episodes_per_seed': 200, 'evaluation_seeds': [1000, 2000, 3000, 4000, 5000],
             'results': {'dqn_policy': {'mean_return': 2.026, 'std_return': 0.041999999999999996},
                         'greedy_heuristic': {'mean_return': 2.026, 'std_return': 0.042},
                         'random_baseline': {'mean_return': 0.9317500000000001, 'std_return': 0.0688},
                         'optimal_oracle': {'mean_return': 2.026, 'std_return': 0.042}}}


def write_artifacts(root: Path, reports: dict):
    for directory, report in reports.items():
        (root / directory).mkdir(parents=True, exist_ok=True)
        (root / directory / 'report.json').write_text(json.dumps(report), encoding='utf-8')


def spec(kind):
    return next(s for s in about.MODEL_SPECS if s['kind'] == kind)


def test_nhanes15_metrics_use_the_selected_threshold_of_predict(tmp_path):
    write_artifacts(tmp_path, {'nhanes15_web': NHANES15_REPORT})
    info = about.model_info(spec('nhanes15_research'), tmp_path, available=True)
    assert info['threshold'] == 0.8
    assert info['metrics_test'] == {'roc_auc': 0.9314, 'f1_pos': 0.7549, 'recall_pos': 0.7515, 'precision_pos': 0.7583,
                                    'accuracy': 0.92, 'brier': 0.0916, 'confusion_matrix': [[1624, 80], [83, 251]],
                                    'auc_ci95': [0.913, 0.9487]}
    assert info['dataset'] | {} == {'name': 'NHANES Hoa Kỳ', 'cycles': ['2015–2016', '2017–2018'],
                                    'label': 'Tự khai đã từng được chẩn đoán (DIQ010)', 'n_train': 1680,
                                    'n_validation': 414, 'n_test': 2038, 'positive_rate_test': 0.1639}
    assert info['baseline'] == {'name': 'Hồi quy logistic', 'split': 'validation', 'roc_auc': 0.9499, 'f1_pos': 0.6704}
    assert info['selection_rule'].startswith('ROC-AUC cao nhất trên tập validation')


def test_nhanes4_metrics_come_from_the_cnn_block(tmp_path):
    write_artifacts(tmp_path, {'nhanes_research': NHANES4_REPORT})
    info = about.model_info(spec('nhanes_research'), tmp_path, available=True)
    m = info['metrics_test']
    assert (info['threshold'], m['roc_auc'], m['f1_pos'], m['recall_pos'], m['precision_pos']) == \
        (0.5, 0.949, 0.7256, 0.8914, 0.6119)
    assert m['brier'] is None and m['auc_ci95'] is None
    assert (info['dataset']['n_test'], info['dataset']['positive_rate_test']) == (2408, 0.1682)
    assert info['baseline']['split'] == 'test'


@pytest.mark.parametrize('kind', ['symptoms', 'brfss'])
def test_mlp_metrics_are_the_positive_class_at_threshold_half(tmp_path, kind):
    write_artifacts(tmp_path, {kind: MLP_REPORT})
    info = about.model_info(spec(kind), tmp_path, available=False)
    assert info['available'] is False and info['threshold'] == 0.5
    assert info['metrics_test'] == {'roc_auc': 0.9232, 'f1_pos': 0.8333, 'recall_pos': 0.7143, 'precision_pos': 1.0,
                                    'accuracy': 0.8039, 'brier': 0.1327, 'confusion_matrix': [[16, 0], [10, 25]],
                                    'auc_ci95': None}
    assert info['dataset']['positive_rate_test'] == 0.6863 and info['dataset']['n_train'] == 160


def test_missing_report_keeps_description_with_null_metrics(tmp_path):
    info = about.model_info(spec('brfss'), tmp_path, available=False)
    assert info['metrics_test'] is None and info['name'] == 'BRFSS (khảo sát lối sống)'
    assert info['limitations'] and all(isinstance(x, str) for x in info['limitations'])


def test_malformed_report_is_partial_not_an_error(tmp_path, caplog):
    write_artifacts(tmp_path, {'brfss': {'neural_network': {'classification_report': {}}}})
    with caplog.at_level(logging.WARNING):
        info = about.model_info(spec('brfss'), tmp_path, available=True)
    assert info['metrics_test'] is None and 'unexpected structure' in caplog.text


def test_non_finite_numbers_become_null(tmp_path):
    report = json.loads(json.dumps(MLP_REPORT))
    report['neural_network']['roc_auc'] = math.nan
    write_artifacts(tmp_path, {'symptoms': report})
    assert about.model_info(spec('symptoms'), tmp_path, True)['metrics_test']['roc_auc'] is None


def test_rl_results_are_named_in_vietnamese(tmp_path):
    write_artifacts(tmp_path, {'rl': RL_REPORT})
    assert about.rl_info(tmp_path) == {'episodes_per_seed': 200, 'seeds': 5, 'results': [
        {'policy': 'DQN', 'mean_return': 2.026, 'std_return': 0.042},
        {'policy': 'Luật tham lam', 'mean_return': 2.026, 'std_return': 0.042},
        {'policy': 'Ngẫu nhiên', 'mean_return': 0.932, 'std_return': 0.069},
        {'policy': 'Tối ưu', 'mean_return': 2.026, 'std_return': 0.042}]}
    assert about.rl_info(tmp_path / 'none') is None


@pytest.mark.skipif(not (ROOT / 'artifacts' / 'nhanes15_web' / 'report.json').exists(), reason='artifacts not mounted')
def test_real_artifacts_match_the_design_table():
    """Số ở bảng design 2d (đọc từ report.json 13/11) phải ra đúng từ artifacts thật."""
    got = {m['kind']: m['metrics_test'] for m in
           (about.model_info(s, ROOT / 'artifacts', True) for s in about.MODEL_SPECS)}
    expected = {'nhanes15_research': (0.931, 0.755, 0.751, 0.758), 'nhanes_research': (0.949, 0.726, 0.891, 0.612),
                'brfss': (0.764, 0.382, 0.757, 0.256), 'symptoms': (0.923, 0.833, 0.714, 1.0)}
    for kind, values in expected.items():
        m = got[kind]
        assert tuple(round(m[k], 3) for k in ('roc_auc', 'f1_pos', 'recall_pos', 'precision_pos')) == values, kind


# --- /api/about: kho tri thức + cache ----------------------------------------------------------------------

class FakeRecord:
    def __init__(self, data):
        self._data = data

    def data(self):
        return dict(self._data)


class FakeDB:
    """execute_query giả: trả bản ghi theo tên câu truy vấn trong about.KB_QUERIES."""

    def __init__(self, fail=False):
        self.fail, self.calls = fail, 0
        self.rows = {
            'documents': [{'reviewed_chunks': 3, 'reviewed_docs': 2, 'web_chunks': 190}],
            'web_pages': [{'n': 25}],
            'topics': [{'name': 'HbA1c'}, {'name': 'Mục tiêu'}],
            'entities': [{'n': 48}],
            'relations': [{'type': 'INCREASES_RISK_OF', 'count': 9}, {'type': 'DIAGNOSES', 'count': 8}],
            'embedding': [{'dim': 1024, 'n': 251}],
            'vector_index': [{'n': 0}],
            'sources': [
                {'id': 'kb2-ruou-bia-bytvn', 'title': 'Rượu bia (Bộ Y tế)', 'url': 'https://byt', 'topic': 'Rượu', 'date': '2026-11-12'},
                {'id': 'kb2-muc-tieu-bytvn', 'title': 'Mục tiêu (Bộ Y tế)', 'url': 'https://byt', 'topic': 'Mục tiêu', 'date': '2026-11-10'},
                {'id': 'kb2-muc-tieu-kiem-soat', 'title': 'Mục tiêu (ADA 2026)', 'url': 'https://ada', 'topic': 'Mục tiêu', 'date': None},
            ],
        }
        self._by_query = {q: name for name, q in about.KB_QUERIES.items()}

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute_query(self, query, database_=None, **params):
        if self.fail:
            raise ConnectionError('Neo4j down')
        self.calls += 1
        name = self._by_query[query]
        if name == 'embedding':
            assert params == {'model': 'bge-m3'}
        return type('Result', (), {'records': [FakeRecord(r) for r in self.rows[name]]})()


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def service(tmp_path, db, clock=None):
    write_artifacts(tmp_path, {'nhanes15_web': NHANES15_REPORT, 'rl': RL_REPORT})
    return about.AboutService(
        artifacts=lambda: tmp_path, availability=lambda: {'nhanes15_research': True}, llm='qwen3:4b-instruct',
        embedding='bge-m3', top_k=3, min_cosine=0.53, number_guard='v1',
        publisher_of=publishers.PublisherRegistry(lambda: publishers.load_publishers(ROOT / 'knowledge')).get,
        db_factory=lambda: db, clock=clock or Clock(),
        now=lambda: datetime(2026, 11, 13, 7, 5, tzinfo=timezone.utc))


def test_kb_counts_and_sources_one_row_per_url(tmp_path):
    payload = service(tmp_path, FakeDB()).get()
    kb = payload['kb']
    assert {k: kb[k] for k in ('reviewed_chunks', 'reviewed_docs', 'web_chunks', 'web_pages', 'topics', 'entities',
                               'relations')} == {'reviewed_chunks': 3, 'reviewed_docs': 2, 'web_chunks': 190,
                                                 'web_pages': 25, 'topics': 2, 'entities': 48, 'relations': 17}
    assert kb['relations_by_type'][0] == {'type': 'INCREASES_RISK_OF', 'count': 9}
    assert kb['topic_names'] == ['HbA1c', 'Mục tiêu']
    assert kb['reviewed_sources'] == [
        {'title': 'Mục tiêu (ADA 2026)', 'url': 'https://ada', 'publisher': 'ADA', 'topic': 'Mục tiêu', 'date': None,
         'chunks': 1},
        {'title': 'Mục tiêu (Bộ Y tế)', 'url': 'https://byt', 'publisher': 'Bộ Y tế', 'topic': 'Mục tiêu',
         'date': '2026-11-12', 'chunks': 2}]
    assert payload['assistant'] == {'llm': 'qwen3:4b-instruct', 'llm_provider': 'Ollama', 'embedding': 'bge-m3',
                                    'embedding_dim': 1024, 'top_k': 3, 'min_cosine': 0.53, 'vector_index': False,
                                    'number_guard': 'v1'}
    assert 'embedding_dim' not in kb and 'vector_index' not in kb


def test_generated_at_is_vietnam_time(tmp_path):
    assert service(tmp_path, FakeDB()).get()['generated_at'] == '2026-11-13T14:05:00+07:00'


def test_neo4j_down_returns_kb_null_and_retries_sooner(tmp_path, caplog):
    clock, db = Clock(), FakeDB(fail=True)
    svc = service(tmp_path, db, clock)
    with caplog.at_level(logging.WARNING):
        payload = svc.get()
    assert payload['kb'] is None and payload['models'] and payload['rl']
    assert payload['assistant']['embedding_dim'] is None and payload['assistant']['vector_index'] is None
    assert 'kb=null' in caplog.text
    db.fail = False
    clock.t = about.CACHE_TTL_KB_DOWN_S - 1
    assert svc.get()['kb'] is None                                   # còn trong TTL ngắn
    clock.t = about.CACHE_TTL_KB_DOWN_S
    assert svc.get()['kb'] is not None                               # hết TTL ngắn → đếm lại


def test_payload_is_cached_until_ttl_expires(tmp_path):
    clock, db = Clock(), FakeDB()
    svc = service(tmp_path, db, clock)
    first = svc.get()
    calls = db.calls
    clock.t = about.CACHE_TTL_S - 0.001
    assert svc.get() is first and db.calls == calls
    clock.t = about.CACHE_TTL_S
    svc.get()
    assert db.calls == 2 * calls
    svc.invalidate()
    svc.get()
    assert db.calls == 3 * calls


def test_payload_has_no_secrets_urls_or_machine_paths(tmp_path, monkeypatch):
    monkeypatch.setenv('NEO4J_PASSWORD', 'super-secret-pw')
    text = json.dumps(service(tmp_path, FakeDB()).get()['assistant'], ensure_ascii=False)
    assert 'super-secret-pw' not in text and 'bolt://' not in text and 'http' not in text
    assert str(tmp_path) not in json.dumps(service(tmp_path, FakeDB()).get(), ensure_ascii=False)


# --- Endpoint + hợp đồng với frontend (wt-da04-web/frontend/src/about.ts) ----------------------------------

ABOUT_KEYS = {'generated_at', 'models', 'rl', 'assistant', 'kb', 'limitations'}
MODEL_KEYS = {'kind', 'name', 'architecture', 'available', 'dataset', 'threshold', 'metrics_test', 'baseline',
              'selection_rule', 'limitations'}
DATASET_KEYS = {'name', 'cycles', 'label', 'n_train', 'n_validation', 'n_test', 'positive_rate_test'}
METRIC_KEYS = {'roc_auc', 'f1_pos', 'recall_pos', 'precision_pos', 'accuracy', 'brier', 'confusion_matrix', 'auc_ci95'}
ASSISTANT_KEYS = {'llm', 'llm_provider', 'embedding', 'embedding_dim', 'top_k', 'min_cosine', 'vector_index', 'number_guard'}
KB_KEYS = {'reviewed_chunks', 'reviewed_docs', 'web_chunks', 'web_pages', 'topics', 'entities', 'relations',
           'relations_by_type', 'topic_names', 'reviewed_sources'}
SOURCE_KEYS = {'title', 'url', 'publisher', 'topic', 'date', 'chunks'}   # 'chunks' thêm, frontend bỏ qua


def test_get_about_endpoint_matches_the_frontend_schema(tmp_path, monkeypatch):
    monkeypatch.setattr(main, 'ABOUT', service(tmp_path, FakeDB()))
    response = TestClient(main.app).get('/api/about')
    assert response.status_code == 200
    body = response.json()
    assert set(body) == ABOUT_KEYS
    assert [m['kind'] for m in body['models']] == ['nhanes15_research', 'nhanes_research', 'brfss', 'symptoms']
    for m in body['models']:
        assert set(m) == MODEL_KEYS and set(m['dataset']) <= DATASET_KEYS
        assert m['metrics_test'] is None or set(m['metrics_test']) == METRIC_KEYS
    assert set(body['assistant']) == ASSISTANT_KEYS
    assert set(body['kb']) == KB_KEYS and all(set(s) == SOURCE_KEYS for s in body['kb']['reviewed_sources'])
    assert set(body['rl']) == {'episodes_per_seed', 'seeds', 'results'}


def test_get_about_is_200_when_neo4j_is_down(tmp_path, monkeypatch):
    monkeypatch.setattr(main, 'ABOUT', service(tmp_path, FakeDB(fail=True)))
    response = TestClient(main.app).get('/api/about')
    assert response.status_code == 200 and response.json()['kb'] is None


def test_default_service_reports_the_running_configuration():
    assistant = main.ABOUT._assistant
    assert assistant['llm'] == main.rag.MODEL and assistant['embedding'] == main.rag.EMBED
    assert assistant['top_k'] == main.RETRIEVE_TOP_K == 3 and assistant['min_cosine'] == main.rag.RAG_THRESHOLD
    assert assistant['number_guard'] in {'v1', 'v2'}


# --- DEF-api-1.1: Neo4j nhận TCP nhưng im lặng / treo; request đồng thời ------------------------------------

import socket
import threading
import time as _time


@pytest.fixture
def silent_neo4j(monkeypatch):
    """Cổng TCP nhận kết nối nhưng không bao giờ trả lời (Neo4j treo, docker pause, GC dài)."""
    server = socket.socket()
    server.bind(('127.0.0.1', 0))
    server.listen(64)
    held, stop = [], threading.Event()

    def accept():
        server.settimeout(0.2)
        while not stop.is_set():
            try:
                held.append(server.accept()[0])
            except OSError:
                continue
    thread = threading.Thread(target=accept, daemon=True)
    thread.start()
    monkeypatch.setenv('NEO4J_URI', f'bolt://127.0.0.1:{server.getsockname()[1]}')
    yield
    stop.set()
    thread.join(1)
    for conn in held:
        conn.close()
    server.close()


def real_driver_service(tmp_path):
    svc = service(tmp_path, None)
    svc._db_factory = about.kb_driver
    return svc


def test_def_api_1_1_silent_neo4j_returns_kb_null_within_deadline(tmp_path, silent_neo4j):
    svc = real_driver_service(tmp_path)
    started = _time.monotonic()
    payload = svc.get()
    elapsed = _time.monotonic() - started
    assert payload['kb'] is None and payload['models']
    assert elapsed <= 3.5, elapsed


def test_def_api_1_1_endpoint_with_silent_neo4j_answers_200_quickly(tmp_path, silent_neo4j, monkeypatch):
    monkeypatch.setattr(main, 'ABOUT', real_driver_service(tmp_path))
    started = _time.monotonic()
    response = TestClient(main.app).get('/api/about')
    assert response.status_code == 200 and response.json()['kb'] is None
    assert _time.monotonic() - started <= 3.5


class HangingDB(FakeDB):
    """Bắt tay xong rồi treo ở query (timeout phía server không cứu được): chỉ deadline phía client chặn được."""

    def __init__(self):
        super().__init__()
        self.release, self.opened = threading.Event(), 0

    def __enter__(self):
        self.opened += 1
        return self

    def execute_query(self, query, database_=None, **params):
        self.release.wait(10)
        raise ConnectionError('released')


def test_def_api_1_1_client_deadline_bounds_a_hung_query(tmp_path):
    db = HangingDB()
    svc = service(tmp_path, db)
    svc._kb_deadline_s = 0.3
    started = _time.monotonic()
    try:
        assert svc.get()['kb'] is None
        assert _time.monotonic() - started < 1.0
    finally:
        db.release.set()


def test_def_api_1_1_concurrent_requests_share_one_build_and_do_not_queue(tmp_path):
    db = HangingDB()
    svc = service(tmp_path, db)
    svc._kb_deadline_s = 0.5
    results, durations = [], []

    def call():
        t = _time.monotonic()
        results.append(svc.get())
        durations.append(_time.monotonic() - t)
    threads = [threading.Thread(target=call) for _ in range(5)]
    try:
        for t in threads:
            t.start()
        for t in threads:
            t.join(5)
        assert len(results) == 5 and all(r['kb'] is None for r in results)
        assert max(durations) < 1.2                     # không xếp hàng 5 × 0,5 s
        assert db.opened == 1                           # single-flight: chỉ một lượt đếm Neo4j
        assert all(r is results[0] for r in results)
    finally:
        db.release.set()


def test_def_api_1_1_lock_is_not_held_while_building(tmp_path):
    db = HangingDB()
    svc = service(tmp_path, db)
    svc._kb_deadline_s = 2.0
    worker = threading.Thread(target=svc.get)
    try:
        worker.start()
        _time.sleep(0.2)                                # đang dựng payload
        assert svc._lock.acquire(timeout=0.1)           # khoá rảnh: invalidate/get khác không bị chặn
        svc._lock.release()
    finally:
        db.release.set()
        worker.join(5)
