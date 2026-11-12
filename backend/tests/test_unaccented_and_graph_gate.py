"""DEF-BE-2 (câu không dấu không có nguồn) và DEF-BE-3 (Graph Agent lách ngưỡng RAG).

Unit test không cần Neo4j/Ollama (fake/stub). Nhóm `live` ở cuối chạy với Neo4j + Ollama thật
(trong container) và tự skip khi không kết nối được.
"""
import json
from pathlib import Path

import pytest

from backend.app import diacritics as dia
from backend.app import knowledge_graph as kg
from backend.app import rag

ROOT = Path(__file__).resolve().parents[2]
SOURCES = (ROOT / 'knowledge/sources.json', ROOT / 'knowledge/sources_v2.json')
GRAPH = ROOT / 'knowledge/graph_entities.json'


@pytest.fixture(scope='module')
def kb_restorer():
    texts = [d[k] for f in SOURCES for d in json.loads(f.read_text(encoding='utf-8')) for k in ('title', 'text')]
    return dia.DiacriticRestorer.from_texts(texts, dia.load_base_vocabulary())


@pytest.fixture(scope='module')
def entities():
    from ml.seed_graph import load_graph
    ents, _ = load_graph(str(GRAPH), tuple(str(f) for f in SOURCES))
    return ents


# --- diacritics: hàm thuần -------------------------------------------------------------------

def test_strip_and_detect_diacritics():
    assert dia.strip_diacritics('Đái tháo đường') == 'Dai thao duong'
    assert dia.has_diacritics('đá') and dia.has_diacritics('Huyết áp')
    assert not dia.has_diacritics('hba1c 6.5% la gi?') and not dia.has_diacritics('')


def test_restore_unaccented_question_from_kb_lexicon(kb_restorer):
    # Câu tái hiện DEF-BE-2
    assert (kb_restorer.restore('huyet ap muc tieu cho nguoi tieu duong la bao nhieu')
            == 'huyết áp mục tiêu cho người tiểu đường là bao nhiêu')
    assert kb_restorer.restore('trieu chung tieu duong la gi') == 'triệu chứng tiểu đường là gì'


def test_restore_keeps_case_and_punctuation_of_unknown_or_ascii_tokens(kb_restorer):
    assert kb_restorer.restore('HbA1c la gi?') == 'HbA1c là gì?'
    assert kb_restorer.restore('xyzabc qwerty') == 'xyzabc qwerty'


def test_restore_leaves_accented_or_partly_accented_question_untouched(kb_restorer):
    for q in ('Huyết áp mục tiêu là bao nhiêu?', 'huyet áp muc tieu', ''):
        assert kb_restorer.restore(q) == q


def test_restore_prefers_longest_ngram_then_most_frequent_form():
    r = dia.DiacriticRestorer.from_texts(['đá bóng. đá. đá', 'da dày', 'dạ dày'])
    assert r.restore('da') == 'đá'                 # 'đá' (3) > 'da' (1)
    assert r.restore('da day') in ('da dày', 'dạ dày')  # cụm 2 âm tiết thắng ghép từng từ
    assert r.restore('da, day') == 'đá, dày'       # không ghép qua dấu câu


def test_restore_tie_break_is_deterministic():
    assert dia.DiacriticRestorer.from_texts(['má', 'mà']).restore('ma') == 'mà'
    assert dia.DiacriticRestorer.from_texts(['mà', 'má']).restore('ma') == 'mà'


# --- DEF-BE-5: từ vựng nền cho từ hỏi đáp thường gặp ------------------------------------------------

HAWK_CASES = [  # 4 ca Hawk báo (trước: "cơ nên ăn chuoi", "tim đạp", "giảm cần", "tới bị mắt ngũ")
    ('nguoi tieu duong co nen an chuoi khong', 'người tiểu đường có nên ăn chuối không'),
    ('tim dap nhanh co sao khong', 'tim đập nhanh có sao không'),
    ('an gi de giam can', 'ăn gì để giảm cân'),
    ('toi bi mat ngu', 'tôi bị mất ngủ'),
]
EARLIER_CASES = [
    ('huyet ap muc tieu cho nguoi tieu duong la bao nhieu', 'huyết áp mục tiêu cho người tiểu đường là bao nhiêu'),
    ('hba1c la gi', 'hba1c là gì'),
    ('cach nau pho bo', 'cách nấu phở bò'),
    ('toi muon tim hieu ve tieu duong', 'tôi muốn tìm hiểu về tiểu đường'),   # tìm (không phải tim)
    ('nguy co bien chung la gi', 'nguy cơ biến chứng là gì'),               # KB "nguy cơ" vẫn thắng
    ('van dong bao nhieu phut moi ngay', 'vận động bao nhiêu phút mỗi ngày'),
    ('an toan khi tap the duc', 'an toàn khi tập thể dục'),                 # KB "an toàn" thắng từ đơn "ăn"
]


@pytest.mark.parametrize('question,expected', HAWK_CASES + EARLIER_CASES)
def test_restore_common_question_words_with_base_vocabulary(kb_restorer, question, expected):
    assert kb_restorer.restore(question).lower() == expected


def test_shipped_base_vocabulary_is_valid_and_keeps_ambiguous_syllables_out():
    vocab = dia.load_base_vocabulary()
    assert 100 <= len(vocab) <= 400
    # cụm không dấu (ra sao, rau xanh...) được phép: chúng khóa cách đọc không dấu, chặn n-gram KB thêm dấu sai
    assert all(dia.has_diacritics(p) or len(p.split()) >= 2 for p in vocab.values())
    # âm tiết đa nghĩa chỉ được nằm trong cụm, không làm từ đơn
    for syllable in ('co', 'tim', 'da', 'mat', 'can', 'ba', 'bo', 'dang', 'the', 'nhung', 'ngay', 'ca', 'pho'):
        assert syllable not in vocab
    assert vocab['tim dap'] == 'tim đập' and vocab['tim hieu'] == 'tìm hiểu'
    assert vocab['da chan'] == 'da chân' and vocab['mat ngu'] == 'mất ngủ'


def test_parse_base_vocabulary_ignores_comments_and_rejects_ambiguous_entries():
    assert dia.parse_base_vocabulary(['# chú thích', '', '  Tôi  ', 'giảm cân  # ghi chú']) == {
        'toi': 'tôi', 'giam can': 'giảm cân'}
    with pytest.raises(ValueError, match='line 2'):
        dia.parse_base_vocabulary(['ba tôi', 'bà tôi'])


def test_base_wins_tie_and_longer_kb_ngram_wins_over_base_word():
    r = dia.DiacriticRestorer({'an': 'an', 'an toan': 'an toàn', 'chuoi': 'chuôi'}, {'an': 'ăn', 'chuoi': 'chuối'})
    assert r.restore('an chuoi') == 'ăn chuối'       # cùng độ dài: nền thắng
    assert r.restore('an toan') == 'an toàn'         # cụm KB dài hơn thắng từ đơn của nền


def test_kb_ngram_may_not_cut_or_misread_a_base_phrase():
    kb = {'de giam can': 'để giảm cần', 'de giam': 'để giảm', 'can': 'cần', 'co nen an': 'cơ nên ăn', 'chuoi': 'chuôi'}
    base = {'giam can': 'giảm cân', 'de': 'để', 'co nen': 'có nên', 'an': 'ăn'}
    r = dia.DiacriticRestorer(kb, base)
    assert r.restore('de giam can') == 'để giảm cân'   # trigram KB đọc khác "giảm cân", bigram KB cắt ngang nó
    assert r.restore('co nen an') == 'có nên ăn'       # trigram KB chứa "co nen" nhưng đọc "cơ nên"
    assert r.restore('giam, can') == 'giam, cần'       # cụm nền không ghép qua dấu câu


def test_base_phrase_already_passed_does_not_block_later_kb_words():
    # "chan bi kho" là cụm nền nhưng greedy đã chọn "da chan"; từ đơn KB "bi" phía sau vẫn được dùng
    r = dia.DiacriticRestorer({'bi': 'bị'}, {'da chan': 'da chân', 'chan bi kho': 'chân bị khô'})
    assert r.restore('da chan bi') == 'da chân bị'


class LexiconDB:
    def __init__(self, rows=None, fail=False):
        self.rows, self.fail, self.calls = rows or [], fail, 0

    def execute_query(self, query, **params):
        self.calls += 1
        if self.fail:
            raise RuntimeError('neo4j down')
        return type('R', (), {'records': self.rows})()


def test_kb_restorer_caches_lexicon_and_skips_db_for_accented_question():
    db = LexiconDB([{'title': 'Huyết áp mục tiêu', 'text': 'Tiểu đường.'}])
    restorer = dia.KnowledgeBaseRestorer()
    assert restorer.restore('Huyết áp?', db) == 'Huyết áp?' and db.calls == 0
    assert restorer.restore('huyet ap muc tieu', db) == 'huyết áp mục tiêu'
    assert restorer.restore('tieu duong', db) == 'tiểu đường'
    assert db.calls == 1


def test_kb_restorer_falls_back_to_question_and_retries_after_failure_or_empty_lexicon(caplog):
    restorer = dia.KnowledgeBaseRestorer()
    assert restorer.restore('huyet ap', LexiconDB(fail=True)) == 'huyet ap'
    assert restorer.restore('huyet ap', LexiconDB([])) == 'huyet ap'
    assert restorer.restore('huyet ap', LexiconDB([{'title': 'Huyết áp', 'text': ''}])) == 'huyết áp'
    assert 'diacritic lexicon' in caplog.text


def test_retrieve_embeds_restored_text_for_unaccented_question(monkeypatch):
    class DB:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def execute_query(self, query, **params):
            return type('R', (), {'records': [{'id': 'a', 'title': 'T', 'url': 'u', 'text': 'x', 'topic': 't',
                                               'review_status': None, 'score': 0.7}]})()

    class Restorer:
        def restore(self, question, db): return 'huyết áp mục tiêu'

    embedded, translated = [], []
    monkeypatch.setattr(rag, 'driver', DB)
    monkeypatch.setattr(rag, 'DIACRITIC_RESTORER', Restorer())
    monkeypatch.setattr(rag, 'embed', lambda text: embedded.append(text) or [0.1] * 1024)
    monkeypatch.setattr(rag, 'english_search_query', lambda q: translated.append(q) or q)
    assert [r['id'] for r in rag.retrieve('huyet ap muc tieu')] == ['a']
    assert embedded == ['huyết áp mục tiêu'] and translated == ['huyết áp mục tiêu']


# --- Knowledge Graph: khớp alias không dấu -----------------------------------------------------

def ids(matched):
    return [e['id'] for e in matched]


def test_unaccented_question_matches_multi_syllable_alias(entities):
    # Câu tái hiện DEF-BE-2: Graph trước đây báo "No matching entity"
    assert 'tang-huyet-ap' in ids(kg.match_entities('huyet ap muc tieu cho nguoi tieu duong la bao nhieu', entities))
    assert 'ha-duong-huyet' in ids(kg.match_entities('bi ha duong huyet thi xu tri the nao', entities))
    assert ids(kg.match_entities('hba1c la gi', entities)) == ['hba1c']


def test_unaccented_matching_skips_single_syllable_accented_aliases(entities):
    # 'tim' (tim mạch) / 'tìm', 'mắt' / 'mất', 'mù' / 'mũ': bỏ dấu sẽ va chạm nên không dùng
    assert kg.match_entities('toi muon tim hieu ve tieu duong', entities) == []
    assert 'bien-chung-mat' not in ids(kg.match_entities('mat ngu co sao khong', entities))
    assert 'bien-chung-mat' in ids(kg.match_entities('tieu duong anh huong vong mac the nao', entities))


def test_unaccented_matching_with_da_collision_and_whole_word():
    ents = [{'id': 'da', 'name': 'Đá', 'aliases': []}, {'id': 'dd', 'name': 'Dạ dày', 'aliases': []}]
    assert kg.match_entities('da', ents) == []                      # 'đá' một âm tiết: không khớp 'da'
    assert ids(kg.match_entities('dau da day', ents)) == ['dd']     # 'dạ dày' hai âm tiết: khớp
    assert kg.match_entities('dau da dayy', ents) == []             # vẫn phải trọn từ


def test_accented_question_still_matches_with_accents(entities):
    assert kg.match_entities('Tôi muốn tìm hiểu về tiểu đường', entities) == []
    assert 'tim-mach' in ids(kg.match_entities('Tiểu đường có hại tim không?', entities))


# --- Cổng liên quan của Graph Agent (DEF-BE-3) --------------------------------------------------

GRAPH_SOURCE = {'title': 'Đồ thị tri thức Neo4j: Tăng huyết áp', 'url': 'https://example.org/g', 'topic': 'Đồ thị tri thức',
                'text': 'Tăng huyết áp làm tăng nguy cơ Bệnh tim mạch.', 'review_status': 'curated_graph', 'facts': [{}],
                'documents': [{'title': 'Tim mạch', 'url': 'https://example.org/d', 'text': 'x', 'topic': 't'}]}


@pytest.fixture
def chat(monkeypatch):
    from fastapi.testclient import TestClient
    from backend.app import main
    calls = {'lookup': 0}

    def lookup(q):
        calls['lookup'] += 1
        return GRAPH_SOURCE

    monkeypatch.setattr(main.rag, 'standalone_question', lambda q, h: q)
    monkeypatch.setattr(main.knowledge_graph, 'lookup', lookup)
    monkeypatch.setattr(main.rag, 'answer', lambda q, sources, history: 'ok' if sources else 'Chưa tìm thấy tài liệu phù hợp')

    def post(retrieved, question='Giá vé xem phim tăng huyết áp không?'):
        monkeypatch.setattr(main.rag, 'retrieve', lambda *a, **k: list(retrieved))
        return TestClient(main.app).post('/api/chat', json={'question': question}).json()
    post.calls = calls
    return post


def test_graph_is_skipped_when_rag_finds_no_source(chat):
    # Câu tái hiện DEF-BE-3: có tên thực thể nhưng ngoài miền, RAG 0 nguồn
    body = chat([])
    assert chat.calls['lookup'] == 0
    assert body['sources'] == []
    assert 'Knowledge Graph Agent (Skipped: no relevant source)' in body['trace']
    assert 'Response Agent (No source)' in body['trace']


def test_graph_is_consulted_when_rag_has_a_source(chat):
    rag_source = {'title': 'Mục tiêu kiểm soát', 'url': 'https://example.org/r', 'text': 'x', 'topic': 't'}
    body = chat([rag_source], 'Huyết áp mục tiêu là bao nhiêu?')
    assert chat.calls['lookup'] == 1
    assert [s['url'] for s in body['sources']] == ['https://example.org/r', 'https://example.org/d', 'https://example.org/g']
    assert 'Knowledge Graph Agent (1 facts, +1 linked docs)' in body['trace']


def test_stream_endpoint_applies_the_same_gate(monkeypatch):
    from fastapi.testclient import TestClient
    from backend.app import main
    monkeypatch.setattr(main.rag, 'standalone_question', lambda q, h: q)
    monkeypatch.setattr(main.rag, 'retrieve', lambda *a, **k: [])
    monkeypatch.setattr(main.knowledge_graph, 'lookup', lambda q: pytest.fail('graph must not be consulted'))
    lines = TestClient(main.app).post('/api/chat/stream', json={'question': 'Giá vé xem phim tăng huyết áp không?'}).text.splitlines()
    done = json.loads(lines[-1])
    assert done['type'] == 'done' and done['sources'] == []
    assert 'Knowledge Graph Agent (Skipped: no relevant source)' in done['trace']


# --- Live: Neo4j + Ollama thật (bổ sung câu không dấu vào bộ đo) ---------------------------------

# (câu không dấu, cùng câu có dấu): bản không dấu phải có nguồn và trùng ít nhất một nguồn với bản có dấu.
UNACCENTED_IN_DOMAIN = [
    ('huyet ap muc tieu cho nguoi tieu duong la bao nhieu', 'huyết áp mục tiêu cho người tiểu đường là bao nhiêu'),
    ('hba1c la gi', 'HbA1c là gì?'),
    ('bi ha duong huyet thi xu tri the nao', 'Bị hạ đường huyết thì xử trí thế nào?'),
    ('trieu chung cua benh tieu duong la gi', 'Triệu chứng của bệnh tiểu đường là gì?'),
    ('nguoi tieu duong co nen an chuoi khong', 'Người tiểu đường có nên ăn chuối không?'),
    ('an gi de giam can', 'Ăn gì để giảm cân?'),
]
UNACCENTED_OUT_OF_DOMAIN = [
    'cach nau pho bo',
    'thoi tiet ha noi ngay mai co mua khong',
    'gia vang sjc hom nay bao nhieu',
    'gia ve xem phim tang huyet ap khong',      # 0.516 < 0.53
    'Giá vé xem phim tăng huyết áp không?',     # 0.501 < 0.53 (câu tái hiện DEF-BE-3)
    'Bóng đá Việt Nam và bệnh tim mạch',        # 0.522 < 0.53
]


@pytest.fixture(scope='module')
def live():
    try:
        rag.embed('ping')
        with rag.driver() as db:
            db.verify_connectivity()
    except Exception as exc:
        pytest.skip(f'Neo4j/Ollama không sẵn sàng: {type(exc).__name__}')


@pytest.mark.parametrize('unaccented,accented', UNACCENTED_IN_DOMAIN)
def test_live_unaccented_question_retrieves_like_accented(live, unaccented, accented):
    got = {r['url'] for r in rag.retrieve(unaccented, top_k=3)}
    expected = {r['url'] for r in rag.retrieve(accented, top_k=3)}
    assert got and got & expected


def test_live_screening_age_question_keeps_curated_ada_and_vn_chunks(live):
    ids = [r['id'] for r in rag.retrieve('Bao nhiêu tuổi thì nên xét nghiệm tiểu đường?', top_k=3)]
    curated = [i for i in ids if not i.startswith('web:')]
    # cả mốc ADA (35 tuổi) lẫn mốc Bộ Y tế VN phải có mặt, không bị chunk web NIDDK đẩy ra ngoài
    assert any(i.startswith('kb2-ai-nen-sang-loc') and not i.endswith('-bytvn') for i in curated)
    assert any(i.endswith('-bytvn') for i in curated)


@pytest.mark.parametrize('question,expected', HAWK_CASES + EARLIER_CASES)
def test_live_restore_with_kb_lexicon_from_neo4j(live, question, expected):
    restorer = dia.KnowledgeBaseRestorer()
    with rag.driver() as db:
        assert restorer.restore(question, db).lower() == expected


def test_live_cooking_question_still_has_no_source(live):
    assert rag.retrieve('Cách nấu phở bò?', top_k=3) == []


@pytest.mark.parametrize('question', UNACCENTED_OUT_OF_DOMAIN)
def test_live_out_of_domain_question_retrieves_nothing(live, question):
    assert rag.retrieve(question, top_k=3) == []
