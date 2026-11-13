"""Dữ liệu cho `GET /api/about` – trang "Dữ liệu và mô hình" (REQ-DA-04, design-ui.md mục 6c).

- models[]: thông tin mô tả tĩnh (tên, dataset, giới hạn – tiếng Việt) + chỉ số đọc từ artifacts/<model>/report.json,
  chuẩn hoá về `metrics_test` tại ĐÚNG ngưỡng mà /api/predict đang dùng (0,5; NHANES 15 dùng selected_threshold).
  Mỗi report có cấu trúc riêng nên mỗi mô hình có một hàm đọc riêng; report thiếu/hỏng → metrics_test null (partial).
- rl: artifacts/rl/report.json.  assistant: tên mô hình từ biến môi trường (không trả URL, mật khẩu, đường dẫn máy).
- kb: đếm trực tiếp Neo4j; Neo4j lỗi → kb null, endpoint vẫn 200.
Toàn bộ payload được cache ngắn (mặc định 5 phút; 30 giây nếu Neo4j lỗi) để không đếm Neo4j mỗi request.
"""
import json
import logging
import math
import os
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor, TimeoutError as FutureTimeout
from datetime import datetime
from pathlib import Path
from typing import Callable
from zoneinfo import ZoneInfo

log = logging.getLogger(__name__)

VN = ZoneInfo('Asia/Ho_Chi_Minh')
CACHE_TTL_S = 300.0
CACHE_TTL_KB_DOWN_S = 30.0
# Hạn chót cho toàn bộ phần đếm Neo4j (DEF-api-1.1). Driver có timeout riêng nhỏ hơn; deadline này chặn cả trường hợp
# server bắt tay xong rồi treo (timeout của Query do server thực thi nên server treo thì không có tác dụng).
KB_DEADLINE_S = 3.0
KB_CONNECT_TIMEOUT_S = 2.0
KB_ACQUIRE_TIMEOUT_S = 2.5
NOT_FOR_DIAGNOSIS = 'Chỉ dùng cho học tập; không dùng để sàng lọc, chẩn đoán hay quyết định điều trị.'


def _num(value, digits: int = 4):
    """Số hữu hạn làm tròn; None/NaN/kiểu lạ → None."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        return None
    return round(float(value), digits)


def _matrix(value):
    if not (isinstance(value, list) and len(value) == 2 and all(isinstance(r, list) and len(r) == 2 for r in value)):
        return None
    return [[int(x) for x in row] for row in value]


def _positive_rate(matrix):
    if not matrix:
        return None
    total = sum(map(sum, matrix))
    return _num(sum(matrix[1]) / total) if total else None


def _metrics(roc_auc, precision, recall, f1, accuracy=None, brier=None, matrix=None, ci=None) -> dict:
    ci = [_num(x) for x in ci] if isinstance(ci, list) and len(ci) == 2 else None
    return {'roc_auc': _num(roc_auc), 'f1_pos': _num(f1), 'recall_pos': _num(recall), 'precision_pos': _num(precision),
            'accuracy': _num(accuracy), 'brier': _num(brier), 'confusion_matrix': _matrix(matrix),
            'auc_ci95': ci if ci and None not in ci else None}


# --- Đọc từng loại report (cấu trúc khác nhau) -----------------------------------------------------------

def _read_mlp_report(report: dict) -> dict:
    """symptoms, brfss (ml/train.py): neural_network.classification_report tại ngưỡng 0,5."""
    nn, pos = report['neural_network'], report['neural_network']['classification_report']['1']
    lr = report.get('logistic_regression') or {}
    lr_pos = (lr.get('classification_report') or {}).get('1') or {}
    matrix = _matrix(nn.get('confusion_matrix'))
    return {
        'threshold': 0.5,
        'metrics_test': _metrics(nn.get('roc_auc'), pos.get('precision'), pos.get('recall'), pos.get('f1-score'),
                                 nn['classification_report'].get('accuracy'), nn.get('brier_score'), matrix),
        'counts': {'n_train': report.get('train'), 'n_validation': report.get('validation'), 'n_test': report.get('test'),
                   'positive_rate_test': _num(report.get('test_positive_fraction')) or _positive_rate(matrix)},
        'baseline': {'name': 'Hồi quy logistic', 'split': 'test', 'roc_auc': _num(lr.get('roc_auc')),
                     'f1_pos': _num(lr_pos.get('f1-score'))} if lr else None,
        'selection_rule': None,
    }


def _read_nhanes4_report(report: dict) -> dict:
    """nhanes_research (ml/train_nhanes.py): khối `cnn` tại ngưỡng 0,5; tập test = chu kỳ 2017–2018."""
    cnn, lr = report['cnn'], report.get('logistic_regression') or {}
    matrix = _matrix(cnn.get('confusion_matrix'))
    test = report.get('test_cycle') or {}
    return {
        'threshold': 0.5,
        'metrics_test': _metrics(cnn.get('roc_auc'), cnn.get('precision'), cnn.get('recall'), cnn.get('f1'),
                                 cnn.get('accuracy'), None, matrix),
        'counts': {'n_train': report.get('train_n'), 'n_validation': report.get('validation_n'),
                   'n_test': test.get('complete') or (sum(map(sum, matrix)) if matrix else None),
                   'positive_rate_test': _positive_rate(matrix)},
        'baseline': {'name': 'Hồi quy logistic', 'split': 'test', 'roc_auc': _num(lr.get('roc_auc')),
                     'f1_pos': _num(lr.get('f1'))} if lr else None,
        'selection_rule': None,
    }


def _read_nhanes15_report(report: dict) -> dict:
    """nhanes15_research (notebook → artifacts/nhanes15_web): test_selected_only tại selected_threshold."""
    test, sizes = report['test_selected_only'], report.get('sizes') or {}
    lr = (report.get('validation_metrics') or {}).get('logistic_regression') or {}
    matrix = _matrix(test.get('confusion_matrix'))
    rule = report.get('selection_rule') or ''
    return {
        'threshold': _num(report.get('selected_threshold')),
        'metrics_test': _metrics(test.get('roc_auc'), test.get('precision'), test.get('recall'), test.get('f1'),
                                 test.get('accuracy'), test.get('brier'), matrix,
                                 report.get('test_auc_bootstrap_stratified_95')),
        'counts': {'n_train': sizes.get('train'), 'n_validation': sizes.get('validation'), 'n_test': sizes.get('test'),
                   'positive_rate_test': _positive_rate(matrix)},
        'baseline': {'name': 'Hồi quy logistic', 'split': 'validation', 'roc_auc': _num(lr.get('roc_auc')),
                     'f1_pos': _num(lr.get('f1'))} if lr else None,
        'selection_rule': ('ROC-AUC cao nhất trên tập validation (hoà thì ưu tiên mô hình cơ sở); '
                           'ngưỡng chọn theo F1 lớn nhất trên validation') if rule.startswith('highest validation ROC-AUC') else None,
    }


# Thứ tự = thứ tự hiển thị (design 2d). `kind` khớp Kind của SCR-4 và của /api/predict.
MODEL_SPECS = [
    {'kind': 'nhanes15_research', 'dir': 'nhanes15_web', 'reader': _read_nhanes15_report,
     'name': 'NHANES đầy đủ (15 chỉ số)', 'architecture': 'CNN 1D',
     'dataset': {'name': 'NHANES Hoa Kỳ', 'cycles': ['2015–2016', '2017–2018'],
                 'label': 'Tự khai đã từng được chẩn đoán (DIQ010)'},
     'limitations': ['Nhãn là tự khai đã từng được chẩn đoán (DIQ010), không phải xét nghiệm xác nhận.',
                     'BMI, cân nặng và chiều cao có tính dư thừa.',
                     'Thí nghiệm hồi cứu; tập kiểm tra đã được xem trước khi chọn mô hình; '
                     'chưa kiểm định lâm sàng hay trên người Việt Nam.', NOT_FOR_DIAGNOSIS]},
    {'kind': 'nhanes_research', 'dir': 'nhanes_research', 'reader': _read_nhanes4_report,
     'name': 'NHANES rút gọn (4 chỉ số)', 'architecture': 'CNN 1D',
     'dataset': {'name': 'NHANES Hoa Kỳ', 'cycles': ['2015–2016 (huấn luyện)', '2017–2018 (kiểm tra)'],
                 'label': 'Tự khai đã từng được chẩn đoán (DIQ010)'},
     'limitations': ['Nhãn tự khai hồi cứu; việc điều trị có thể làm thay đổi các chỉ số đo.',
                     'Chỉ gồm ca đủ dữ liệu trong nhóm xét nghiệm lúc đói; không dùng trọng số khảo sát, '
                     'không đại diện dân số.',
                     'HbA1c và glucose là chính các xét nghiệm chẩn đoán nên có thể trùng với chẩn đoán trước đó.',
                     'Thứ tự đặc trưng đưa vào CNN là tuỳ ý; chưa kiểm định lâm sàng hay ngoài dữ liệu cho Việt Nam.',
                     NOT_FOR_DIAGNOSIS]},
    {'kind': 'brfss', 'dir': 'brfss', 'reader': _read_mlp_report,
     'name': 'BRFSS (khảo sát lối sống)', 'architecture': 'MLP',
     'dataset': {'name': 'BRFSS (CDC)', 'cycles': ['2021', '2022', '2023'],
                 'label': 'Tự khai đã từng được chẩn đoán (DIABETE4)'},
     'limitations': ['Dữ liệu khảo sát tự khai, cắt ngang; không dùng trọng số khảo sát khi huấn luyện và đánh giá.',
                     'Chưa hiệu chỉnh cho chẩn đoán hay cho người Việt Nam.', NOT_FOR_DIAGNOSIS]},
    {'kind': 'symptoms', 'dir': 'symptoms', 'reader': _read_mlp_report,
     'name': 'UCI (triệu chứng)', 'architecture': 'MLP',
     'dataset': {'name': 'UCI Early Stage Diabetes Risk Prediction', 'cycles': None,
                 'label': 'Kết luận dương tính/âm tính của phòng khám'},
     'limitations': ['Dữ liệu nhỏ (251 hồ sơ không trùng) từ một phòng khám ở Sylhet, Bangladesh.',
                     'Chưa hiệu chỉnh cho chẩn đoán hay cho người Việt Nam.', NOT_FOR_DIAGNOSIS]},
]

RL_POLICIES = [('dqn_policy', 'DQN'), ('greedy_heuristic', 'Luật tham lam'), ('random_baseline', 'Ngẫu nhiên'),
               ('optimal_oracle', 'Tối ưu')]


def _read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError:
        return None


def model_info(spec: dict, root: Path, available: bool) -> dict:
    """Một phần tử models[]. Report thiếu hoặc sai cấu trúc → metrics_test null, phần mô tả vẫn trả."""
    info = {'kind': spec['kind'], 'name': spec['name'], 'architecture': spec['architecture'], 'available': available,
            'dataset': dict(spec['dataset']), 'threshold': None, 'metrics_test': None, 'baseline': None,
            'selection_rule': None, 'limitations': list(spec['limitations'])}
    try:
        report = _read_json(root / spec['dir'] / 'report.json')
        if report is None:
            return info
        read = spec['reader'](report)
    except (KeyError, TypeError, ValueError, AttributeError):
        log.warning('Model report for %s has an unexpected structure; metrics omitted', spec['kind'], exc_info=True)
        return info
    info['dataset'].update({k: (int(v) if isinstance(v, (int, float)) and k.startswith('n_') else v)
                            for k, v in read['counts'].items()})
    info.update({k: read[k] for k in ('threshold', 'metrics_test', 'baseline', 'selection_rule')})
    return info


def rl_info(root: Path) -> dict | None:
    try:
        report = _read_json(root / 'rl' / 'report.json')
        if report is None:
            return None
        results = [{'policy': label, 'mean_return': _num(report['results'][key]['mean_return'], 3),
                    'std_return': _num(report['results'][key].get('std_return'), 3)}
                   for key, label in RL_POLICIES if key in report['results']]
        return {'episodes_per_seed': report.get('episodes_per_seed'),
                'seeds': len(report.get('evaluation_seeds') or []) or None, 'results': results}
    except (KeyError, TypeError, ValueError, AttributeError):
        log.warning('RL report has an unexpected structure; rl omitted', exc_info=True)
        return None


# --- Kho tri thức (Neo4j) ----------------------------------------------------------------------------

REVIEWED = "coalesce(d.review_status, '') <> 'unreviewed_web'"
KB_QUERIES = {
    'documents': f'''MATCH (d:Document) RETURN
        count(CASE WHEN {REVIEWED} THEN 1 END) AS reviewed_chunks,
        count(DISTINCT CASE WHEN {REVIEWED} THEN d.url END) AS reviewed_docs,
        count(CASE WHEN NOT {REVIEWED} THEN 1 END) AS web_chunks''',
    'web_pages': 'MATCH (w:WebSource) RETURN count(w) AS n',
    'topics': 'MATCH (t:Topic) RETURN t.name AS name ORDER BY name',
    'entities': 'MATCH (e:Entity) RETURN count(e) AS n',
    'relations': 'MATCH (:Entity)-[r]->(:Entity) RETURN type(r) AS type, count(*) AS count ORDER BY count DESC, type',
    'embedding': '''MATCH (d:Document) WHERE d.embedding_model = $model AND d.embedding IS NOT NULL
        RETURN size(d.embedding) AS dim, count(*) AS n ORDER BY n DESC LIMIT 1''',
    'vector_index': "SHOW INDEXES YIELD type WHERE type = 'VECTOR' RETURN count(*) AS n",
    'sources': f'''MATCH (d:Document) WHERE {REVIEWED}
        RETURN d.id AS id, d.title AS title, d.url AS url, d.topic AS topic, d.date AS date ORDER BY d.url, d.id''',
}


def reviewed_sources(rows: list[dict], publisher_of: Callable[[str], str | None]) -> list[dict]:
    """Một dòng mỗi URL: tiêu đề/chủ đề của đoạn có id nhỏ nhất, ngày mới nhất, publisher của đoạn đầu có giá trị."""
    by_url: dict[str, list[dict]] = {}
    for row in rows:
        by_url.setdefault(row['url'] or '', []).append(row)
    out = []
    for url, chunks in by_url.items():
        chunks = sorted(chunks, key=lambda r: r['id'])
        first = chunks[0]
        dates = [r['date'] for r in chunks if r.get('date')]
        out.append({'title': first['title'], 'url': url,
                    'publisher': next((p for p in (publisher_of(r['id']) for r in chunks) if p), None),
                    'topic': first.get('topic'), 'date': max(dates) if dates else None, 'chunks': len(chunks)})
    return sorted(out, key=lambda s: ((s['publisher'] or '~'), s['title'] or '', s['url']))


def kb_stats(db, embed_model: str, publisher_of: Callable[[str], str | None]) -> dict:
    run = lambda name, **params: [r.data() for r in db.execute_query(KB_QUERIES[name], database_='neo4j', **params).records]
    docs = run('documents')[0]
    relations = run('relations')
    embedding = run('embedding', model=embed_model)
    topics = [r['name'] for r in run('topics')]
    return {
        'reviewed_chunks': docs['reviewed_chunks'], 'reviewed_docs': docs['reviewed_docs'],
        'web_chunks': docs['web_chunks'], 'web_pages': run('web_pages')[0]['n'],
        'topics': len(topics), 'entities': run('entities')[0]['n'],
        'relations': sum(r['count'] for r in relations), 'relations_by_type': relations,
        'topic_names': topics,
        'reviewed_sources': reviewed_sources(run('sources'), publisher_of),
        'embedding_dim': embedding[0]['dim'] if embedding else None,
        'vector_index': run('vector_index')[0]['n'] > 0,
    }


def kb_driver():
    """Driver riêng có timeout ngắn: Neo4j sập thì /api/about trả nhanh (driver mặc định thử lại tới 30 s)."""
    from neo4j import GraphDatabase
    # connection_timeout chỉ chặn bước mở socket; bước lấy connection (bolt handshake) cần connection_acquisition_timeout
    # (mặc định 60 s) – thiếu nó thì server nhận TCP mà im lặng sẽ giữ request ~60 s (DEF-api-1.1).
    return GraphDatabase.driver(os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
                                auth=(os.getenv('NEO4J_USER', 'neo4j'), os.getenv('NEO4J_PASSWORD', '')),
                                connection_timeout=KB_CONNECT_TIMEOUT_S,
                                connection_acquisition_timeout=KB_ACQUIRE_TIMEOUT_S, max_transaction_retry_time=0.0)


# --- Ghép payload + cache --------------------------------------------------------------------------------

class AboutService:
    """Dựng payload /api/about và cache theo TTL. Phụ thuộc truyền vào để test không cần file thật hay Neo4j.

    Đồng thời (DEF-api-1.1): khoá chỉ bảo vệ trạng thái, KHÔNG giữ trong lúc dựng payload. Mỗi lúc chỉ một request
    dựng (single-flight); request khác tới trong lúc đó chờ chính kết quả ấy, nên không có lượt đếm Neo4j chồng nhau
    và không request nào chờ lâu hơn một lần dựng (≤ KB_DEADLINE_S cộng phần đọc file).
    """

    def __init__(self, *, artifacts: Callable[[], Path], availability: Callable[[], dict], llm: str, embedding: str,
                 top_k: int, min_cosine: float, number_guard: str, publisher_of: Callable[[str], str | None],
                 db_factory=kb_driver, clock: Callable[[], float] = time.monotonic,
                 now: Callable[[], datetime] = lambda: datetime.now(VN), kb_deadline_s: float = KB_DEADLINE_S):
        self._artifacts, self._availability = artifacts, availability
        self._assistant = {'llm': llm, 'llm_provider': 'Ollama', 'embedding': embedding, 'top_k': top_k,
                           'min_cosine': min_cosine, 'number_guard': number_guard}
        self._publisher_of, self._db_factory, self._clock, self._now = publisher_of, db_factory, clock, now
        self._kb_deadline_s = kb_deadline_s
        # Thread nền đếm Neo4j; nếu quá hạn thì bị bỏ lại và tự kết thúc theo timeout của driver (≤ vài giây).
        self._kb_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix='about-kb')
        self._cached: tuple[float, dict] | None = None
        self._inflight: Future | None = None
        self._lock = threading.Lock()

    def invalidate(self) -> None:
        with self._lock:
            self._cached = None

    def get(self) -> dict:
        with self._lock:
            if self._cached and self._clock() < self._cached[0]:
                return self._cached[1]
            pending, owner = self._inflight, self._inflight is None
            if owner:
                pending = self._inflight = Future()
        if not owner:
            return pending.result()
        try:
            payload = self._build()
        except BaseException as exc:
            pending.set_exception(exc)
            raise
        finally:
            with self._lock:
                self._inflight = None
        ttl = CACHE_TTL_S if payload['kb'] is not None else CACHE_TTL_KB_DOWN_S
        with self._lock:
            self._cached = (self._clock() + ttl, payload)
        pending.set_result(payload)
        return payload

    def _count_kb(self) -> dict:
        with self._db_factory() as db:
            return kb_stats(db, self._assistant['embedding'], self._publisher_of)

    def _kb(self) -> dict | None:
        future = self._kb_pool.submit(self._count_kb)
        try:
            return future.result(timeout=self._kb_deadline_s)
        except FutureTimeout:
            future.cancel()
            log.warning('Knowledge base statistics took longer than %.1f s (Neo4j); returning kb=null',
                        self._kb_deadline_s)
            return None
        except Exception:
            log.warning('Knowledge base statistics unavailable (Neo4j); returning kb=null', exc_info=True)
            return None

    def _build(self) -> dict:
        root, available = self._artifacts(), self._availability()
        kb = self._kb()
        assistant = dict(self._assistant)
        assistant['embedding_dim'] = kb.pop('embedding_dim') if kb else None
        assistant['vector_index'] = kb.pop('vector_index') if kb else None
        return {
            'generated_at': self._now().astimezone(VN).isoformat(timespec='seconds'),
            'models': [model_info(spec, root, bool(available.get(spec['kind']))) for spec in MODEL_SPECS],
            'rl': rl_info(root),
            'assistant': assistant,
            'kb': kb,
            'limitations': [],
        }
