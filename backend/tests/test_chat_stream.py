"""REQ-DA-03-T2: /api/chat/stream phát theo câu qua hậu kiểm số.

Mọi cộng tác viên của T1 (guard, splitter, GuardContext.for_turn, REMOVED_NOTE, safe_fallback, unreviewed_tail,
CheckedAnswer, answer_parts) là fake theo interface design-data.md §3, truyền qua app.dependency_overrides;
không monkeypatch module của T1, không gọi Ollama/Neo4j thật. Chỉ retrieve/standalone_question (pipeline có
sẵn) được thay như các test API khác.

Truy vết UT-n ↔ AC/EC/NFR: xem tên test (tiền tố utN) và bảng ở cuối file.
"""
import asyncio
import json
import logging
from dataclasses import dataclass, replace

import pytest
from fastapi.testclient import TestClient

from backend.app import main

# --- Fake theo design-data.md §3.4 ---------------------------------------------------------------


@dataclass(frozen=True)
class FakeVerdict:
    ok: bool
    unsupported: tuple[str, ...]


class FakeGuard:
    """Vi phạm khi câu chứa chuỗi trong self.bad (§3.4)."""

    def __init__(self, bad=('77', '70–99', '88')):
        self.bad = bad
        self.checked: list[str] = []

    def check(self, text, ctx):
        assert ctx is REVIEWED_CTX
        self.checked.append(text)
        unsupported = tuple(b for b in self.bad if b in text)
        return FakeVerdict(not unsupported, unsupported)


class FakeSplitter:
    """Tách sau '. ' và sau '\\n'; ''.join(câu) == ''.join(token) (§3.2). Đủ cho test luồng."""

    def __init__(self):
        self.buffer = ''

    def feed(self, token):
        self.buffer += token
        out = []
        while True:
            cuts = [i + 2 for i in [self.buffer.find('. ')] if i >= 0] + [i + 1 for i in [self.buffer.find('\n')] if i >= 0]
            if not cuts:
                return out
            cut = min(cuts)
            out.append(self.buffer[:cut])
            self.buffer = self.buffer[cut:]

    def flush(self):
        rest, self.buffer = self.buffer, ''
        return [rest] if rest else []


class FakeCheckedAnswer(str):
    """Theo chữ ký CheckedAnswer của T1 (§3.3)."""

    def __new__(cls, text, status, numbers=None, removed=0, total=0):
        obj = super().__new__(cls, text)
        obj.check = {'status': status, 'numbers': list(numbers or []), 'removed': removed, 'total': total}
        return obj


REVIEWED_CTX = object()
REMOVED_NOTE = 'Một phần nội dung có con số chưa được nguồn xác nhận nên đã được lược bỏ; vui lòng xem nguồn bên dưới.'
TAIL = '\n\nCác nguồn web tự động khác được hiển thị để tham khảo trực tiếp, chưa dùng để tổng hợp câu trả lời.'
REFUSAL = 'Chưa tìm thấy tài liệu phù hợp trong kho tri thức của hệ thống cho câu hỏi này.'
REVIEWED = {'title': 'Đường huyết bình thường', 'url': 'https://diabetes.org/bt', 'text': '99 mg/dL', 'topic': 't',
            'review_status': 'reviewed'}
WEB = {'title': 'Web', 'url': 'https://example.org/web', 'text': 'x', 'topic': 't', 'review_status': 'unreviewed_web'}


def fake_for_turn(question, sources, history):
    return REVIEWED_CTX if any(s.get('review_status') != 'unreviewed_web' for s in sources) else None


def fake_safe_fallback(sources):
    reviewed = [(i, s) for i, s in enumerate(sources) if s.get('review_status') != 'unreviewed_web']
    return 'Câu trả lời an toàn: mở nguồn ' + '; '.join(f"[{i + 1}] {s['title']}" for i, s in reviewed[:3])


def fake_tail(sources):
    reviewed = [s for s in sources if s.get('review_status') != 'unreviewed_web']
    return TAIL if reviewed and len(reviewed) < len(sources) else None


class FakeLLM:
    """answer_parts giả: phát token theo thứ tự, ghi lại lời gọi; `on_token(i)` chạy TRƯỚC khi phát token i."""

    def __init__(self, tokens, error_after=None, on_token=None):
        self.tokens, self.error_after, self.on_token = list(tokens), error_after, on_token
        self.calls: list[dict] = []
        self.closed = False

    def __call__(self, question, sources, history=None, include_tail=True):
        self.calls.append({'question': question, 'include_tail': include_tail})
        return self._run(sources, include_tail)

    def _run(self, sources, include_tail):
        try:
            for i, token in enumerate(self.tokens):
                if self.error_after is not None and i == self.error_after:
                    raise RuntimeError('Ollama stream ended prematurely')
                if self.on_token:
                    self.on_token(i)
                yield token
            if not sources:
                return
            tail = fake_tail(sources)
            if include_tail and tail:
                yield tail
        finally:
            self.closed = True


def make_deps(llm, guard=None, **overrides):
    deps = main.StreamDeps(answer_parts=llm, context_for_turn=fake_for_turn, guard=guard or FakeGuard(),
                           splitter_factory=FakeSplitter, removed_note=REMOVED_NOTE, safe_fallback=fake_safe_fallback,
                           unreviewed_tail=fake_tail, checked_answer=FakeCheckedAnswer)
    return replace(deps, **overrides)


@pytest.fixture
def pipeline(monkeypatch):
    """Pipeline giả tới trước Response Agent; trả hàm đặt nguồn truy xuất được."""
    monkeypatch.setattr(main.rag, 'standalone_question', lambda q, h: q)
    recorded = []
    monkeypatch.setattr(main.history, 'record', lambda kind: recorded.append(kind))
    state = {'sources': [REVIEWED], 'recorded': recorded}
    monkeypatch.setattr(main.rag, 'retrieve', lambda *a, **k: [dict(s) for s in state['sources']])
    yield state
    main.app.dependency_overrides.clear()


def post_stream(deps, question='Đường huyết lúc đói bình thường là bao nhiêu?', history=None):
    main.app.dependency_overrides[main.stream_deps_provider] = lambda: (lambda: deps)
    response = TestClient(main.app).post('/api/chat/stream', json={'question': question, 'history': history or []})
    assert response.status_code == 200
    return [json.loads(line) for line in response.text.splitlines()]


def stream_lines(deps, question='Đường huyết lúc đói bình thường là bao nhiêu?'):
    """Generator NDJSON của stream (không qua HTTP) để kiểm thứ tự phát so với token của LLM."""
    return main.stream_events({'question': question, 'history': []}, lambda: deps)


def deltas(events):
    return [e['text'] for e in events if e['type'] == 'delta']


def number_check(events):
    return [t for t in events[-1]['trace'] if 'Number check' in t]


# --- AC-7: phát theo câu, câu nào cũng qua guard trước khi phát ----------------------------------

THREE_CLEAN = ['Câu ', 'một [1]', '. ', 'Câu hai ', 'có 126 mg/dL [1]', '. ', 'Câu ', 'ba [2].']


def test_ut1_ac7_three_clean_sentences_arrive_as_separate_deltas_before_done(pipeline):
    llm = FakeLLM(THREE_CLEAN)
    guard = FakeGuard()
    events = post_stream(make_deps(llm, guard))
    assert deltas(events) == ['Câu một [1]. ', 'Câu hai có 126 mg/dL [1]. ', 'Câu ba [2].']
    assert events[-1]['type'] == 'done'
    assert ''.join(deltas(events)).strip() == ''.join(THREE_CLEAN).strip()
    assert guard.checked == deltas(events)                       # mỗi câu phát ra đều đã qua guard
    assert number_check(events) == ['Response Agent (Number check: passed)']


def test_ut2_ac7_first_delta_is_sent_before_the_llm_starts_sentence_two(pipeline):
    sent: list[str] = []
    snapshot = {}
    llm = FakeLLM(THREE_CLEAN, on_token=lambda i: snapshot.setdefault(i, list(sent)))
    lines = stream_lines(make_deps(llm))
    for line in lines:
        sent.append(line)
    first_token_of_sentence_two = THREE_CLEAN.index('Câu hai ')
    assert [json.loads(x)['text'] for x in snapshot[first_token_of_sentence_two]] == ['Câu một [1]. ']


def test_ut3_ac7_no_character_of_an_unfinished_sentence_is_sent(pipeline):
    # LLM "dừng" sau "Câu hai có 1": tại thời điểm sinh token kế tiếp, client chưa được nhận gì của câu hai.
    tokens = ['Câu một [1]. ', 'Câu hai có 1', '26 mg/dL [1].']
    sent: list[str] = []
    snapshot = {}
    llm = FakeLLM(tokens, on_token=lambda i: snapshot.setdefault(i, ''.join(sent)))
    for line in stream_lines(make_deps(llm)):
        sent.append(json.loads(line).get('text', ''))
    assert 'Câu hai' not in snapshot[2]
    assert snapshot[2] == 'Câu một [1]. '


def test_ut4_ac7_leading_whitespace_is_trimmed_and_blank_pieces_join_the_next_sentence(pipeline):
    llm = FakeLLM(['\n', 'A [1].\n', '\n', '- B [1].\n', '\n'])
    guard = FakeGuard()
    events = post_stream(make_deps(llm, guard))
    assert deltas(events) == ['A [1].\n', '\n- B [1].\n']
    assert guard.checked == deltas(events)                       # khoảng trắng không thành câu riêng để kiểm
    assert 'Response Agent (Number check: passed)' in events[-1]['trace']


# --- AC-8: câu vi phạm bị lược, câu sạch vẫn phát -----------------------------------------------

def test_ut5_ac8_violating_sentence_is_removed_and_note_appended(pipeline):
    llm = FakeLLM(['A [1]. ', 'Bình thường là 70–99 mg/dL [1]. ', 'C [2].'])
    events = post_stream(make_deps(llm))
    text = ''.join(deltas(events))
    assert 'A [1].' in text and 'C [2].' in text
    assert '70–99' not in text
    assert deltas(events)[-1] == '\n\n' + REMOVED_NOTE
    assert text.count(REMOVED_NOTE) == 1
    assert number_check(events) == ['Response Agent (Number check: filtered 1/3 sentences, unsupported: 70–99)']


def test_ut6_ac8_all_content_sentences_violating_returns_the_safe_answer(pipeline):
    pipeline['sources'] = [REVIEWED, WEB]
    llm = FakeLLM(['Ngưỡng 77 mg/dL [1]. ', 'Và 88 mg/dL, lại 77 [1].'])
    events = post_stream(make_deps(llm))
    assert deltas(events) == [fake_safe_fallback([REVIEWED, WEB])]          # không tail, không note
    assert number_check(events) == ['Response Agent (Number check: blocked, unsupported: 77, 88)']
    assert not any('Number check: filtered' in t for t in events[-1]['trace'])


def test_ut7_ac8_unsupported_numbers_are_unique_in_order_across_sentences(pipeline):
    llm = FakeLLM(['A [1]. ', 'Có 88 và 77 [1]. ', 'Lại 77 [1]. ', 'D [1].'])
    events = post_stream(make_deps(llm))
    assert number_check(events) == ['Response Agent (Number check: filtered 2/4 sentences, unsupported: 77, 88)']


def test_ut8_ac8_ec20_stream_never_regenerates(pipeline):
    llm = FakeLLM(['Ngưỡng 77 mg/dL [1].'])
    post_stream(make_deps(llm))
    assert len(llm.calls) == 1 and llm.calls[0]['include_tail'] is False


def test_ut9_nfr10_removed_sentence_logs_index_and_numbers_without_content(pipeline, caplog):
    question = 'Câu hỏi riêng tư của tôi về đường huyết 250 thì sao?'
    llm = FakeLLM(['A [1]. ', 'Bình thường là 70–99 mg/dL [1]. ', 'C [2].'])
    with caplog.at_level(logging.WARNING, logger=main.log.name):
        post_stream(make_deps(llm), question=question)
    removed = [r for r in caplog.records if 'removed sentence' in r.getMessage()]
    assert len(removed) == 1 and removed[0].levelno == logging.WARNING
    assert removed[0].getMessage() == "Number check: removed sentence 2, unsupported ['70–99']"
    full_log = '\n'.join(r.getMessage() for r in caplog.records)
    assert question not in full_log and 'Bình thường là' not in full_log


# --- EC-16: dòng nguồn web tự động do code thêm ------------------------------------------------

def test_ut10_ec16_unreviewed_tail_is_sent_last_after_the_note(pipeline):
    pipeline['sources'] = [REVIEWED, WEB]
    llm = FakeLLM(['A [1]. ', 'Có 77 [1].'])
    events = post_stream(make_deps(llm))
    assert deltas(events)[-2:] == ['\n\n' + REMOVED_NOTE, TAIL]
    assert ''.join(deltas(events)).count(TAIL) == 1                         # answer_parts không phát tail lần nữa


def test_ut11_ec16_tail_is_sent_when_all_sentences_pass(pipeline):
    pipeline['sources'] = [REVIEWED, WEB]
    events = post_stream(make_deps(FakeLLM(['A [1].'])))
    assert deltas(events) == ['A [1].', TAIL]
    assert number_check(events) == ['Response Agent (Number check: passed)']


# --- AC-9 / NFR-7: hợp đồng sự kiện và trace ----------------------------------------------------

@pytest.mark.parametrize('tokens', [THREE_CLEAN, ['A [1]. ', 'Có 77 [1].'], ['Có 77 [1].']])
def test_ut12_ac9_events_keep_the_v1_schema_and_end_with_exactly_one_done(pipeline, tokens):
    events = post_stream(make_deps(FakeLLM(tokens)))
    assert all(e['type'] in {'delta', 'done', 'error'} for e in events)
    assert all(set(e) == {'type', 'text'} for e in events if e['type'] == 'delta')
    assert [e['type'] for e in events].count('done') == 1 and events[-1]['type'] == 'done'
    assert set(events[-1]) == {'type', 'sources', 'trace', 'disclaimer'}
    # Trường v1 luôn có; REQ-DA-04 chỉ thêm publisher (B-2) và facts cho nguồn đồ thị (B-3).
    v1 = {'title', 'url', 'topic', 'review_status', 'fetched_at'}
    assert v1 <= set(events[-1]['sources'][0]) <= v1 | {'publisher', 'facts'}


def test_ut13_ac9_trace_matches_v1_steps_with_one_number_check_line(pipeline):
    events = post_stream(make_deps(FakeLLM(['A [1]. ', 'Có 77 [1]. ', 'C [1].'])))
    trace = events[-1]['trace']
    assert trace == ['Coordinator', 'Rule Agent', 'Rule Agent (Approved)', 'Knowledge Agent (Retrieved 1 sources)',
                     'Knowledge Graph Agent (No matching entity)', 'Response Agent (Cited Generation)',
                     'Response Agent (Number check: filtered 1/3 sentences, unsupported: 77)']


@pytest.mark.parametrize('check,line', [
    ({'status': 'passed', 'numbers': []}, 'Response Agent (Number check: passed)'),
    ({'status': 'regenerated', 'numbers': ['77']}, 'Response Agent (Number check: regenerated, unsupported: 77)'),
    ({'status': 'blocked', 'numbers': ['77', '88']}, 'Response Agent (Number check: blocked, unsupported: 77, 88)'),
    ({'status': 'filtered', 'numbers': ['70–99'], 'removed': 1, 'total': 3},
     'Response Agent (Number check: filtered 1/3 sentences, unsupported: 70–99)'),
])
def test_ut14_nfr7_number_check_trace_strings_are_fixed(check, line):
    answer = FakeCheckedAnswer('x', check['status'], check['numbers'], check.get('removed', 0), check.get('total', 0))
    assert main.number_check_trace(answer) == [line]


def test_ut15_nfr7_filtered_line_is_not_a_blocked_trace_for_the_frontend():
    # frontend/src/trace.ts: isBlockedTrace tìm chữ "blocked"; formatTrace tách "Tên (chi tiết)".
    [line] = main.number_check_trace(FakeCheckedAnswer('x', 'filtered', ['77'], 1, 2))
    assert 'blocked' not in line.lower()
    assert line.startswith('Response Agent (Number check: ') and line.endswith(')') and line.count('(') == 1


def test_ut16_number_check_trace_skips_and_rejects_unknown_status():
    assert main.number_check_trace('plain text') == []
    assert main.number_check_trace(FakeCheckedAnswer('x', 'skipped')) == []
    with pytest.raises(ValueError):
        main.number_check_trace(FakeCheckedAnswer('x', 'weird'))


# --- AC-10 / EC-18 / NFR-8: lỗi giữa chừng --------------------------------------------------------

def test_ut17_ac10_error_after_one_sentence_sends_it_then_exactly_one_error(pipeline):
    llm = FakeLLM(['A [1]. ', 'B có 12', '6 mg/dL [1].'], error_after=2)   # lỗi ngay sau token "B có 12"
    events = post_stream(make_deps(llm))
    assert [e['type'] for e in events] == ['delta', 'error']
    assert events[0]['text'] == 'A [1]. '
    assert 'B có 12' not in json.dumps(events, ensure_ascii=False)
    assert set(events[-1]) == {'type', 'message'} and events[-1]['message'] == main.STREAM_ERROR_MESSAGE
    assert pipeline['recorded'] == []                                         # lượt lỗi không ghi history
    assert llm.closed


def test_ut18_nfr8_error_before_any_token_ends_with_one_error_event(pipeline):
    events = post_stream(make_deps(FakeLLM(['x'], error_after=0)))
    assert [e['type'] for e in events] == ['error']


def test_ut19_nfr8_guard_failure_is_an_error_event_not_a_hang(pipeline):
    class BrokenGuard:
        def check(self, text, ctx):
            raise RuntimeError('guard bug')
    events = post_stream(make_deps(FakeLLM(['A [1].']), guard=BrokenGuard()))
    assert [e['type'] for e in events] == ['error']


def test_ut20_nfr8_missing_t1_module_ends_with_error_only_on_the_rag_path(pipeline):
    def broken():
        raise ImportError('T1 chưa ghép')
    main.app.dependency_overrides[main.stream_deps_provider] = lambda: broken
    client = TestClient(main.app)
    rag_events = [json.loads(x) for x in client.post('/api/chat/stream', json={'question': 'HbA1c là gì?'}).text.splitlines()]
    assert [e['type'] for e in rag_events] == ['error']
    hello = [json.loads(x) for x in client.post('/api/chat/stream', json={'question': 'Xin chào'}).text.splitlines()]
    assert hello[-1]['type'] == 'done'


# --- EC-17: client ngắt kết nối ------------------------------------------------------------------

def test_ut21_ec17_closing_the_stream_closes_the_llm_and_skips_history(pipeline):
    llm = FakeLLM(THREE_CLEAN)
    lines = stream_lines(make_deps(llm))
    first = json.loads(next(lines))
    assert first['type'] == 'delta'
    lines.close()                                                              # GeneratorExit như khi client ngắt
    assert llm.closed
    assert pipeline['recorded'] == []


def test_ut22_ec17_async_wrapper_closes_the_sync_generator_on_disconnect():
    closed = []

    def lines():
        try:
            yield 'a\n'
            yield 'b\n'
        finally:
            closed.append(True)

    async def consume_first_then_disconnect():
        stream = main._closing(lines())
        assert await stream.__anext__() == 'a\n'
        await stream.aclose()                                                  # Starlette huỷ response khi client ngắt

    asyncio.run(consume_first_then_disconnect())
    assert closed == [True]


def test_ut23_ec17_successful_stream_records_history_once(pipeline):
    post_stream(make_deps(FakeLLM(['A [1].'])))
    assert pipeline['recorded'] == ['chat']


# --- EC-19: hai request song song ----------------------------------------------------------------

def test_ut24_ec19_interleaved_streams_do_not_mix_sentences(pipeline):
    first = stream_lines(make_deps(FakeLLM(['A1 [1]. ', 'A2 [1]. ', 'A3 [1].'])))
    second = stream_lines(make_deps(FakeLLM(['B1 [1]. ', 'B2 [1].'])))
    got = {'A': [], 'B': []}
    for key, lines in [('A', first), ('B', second)] * 6:
        line = next(lines, None)
        if line:
            got[key].append(json.loads(line))
    assert deltas(got['A']) == ['A1 [1]. ', 'A2 [1]. ', 'A3 [1].']
    assert deltas(got['B']) == ['B1 [1]. ', 'B2 [1].']


def test_ut25_ec19_each_request_gets_its_own_splitter(pipeline):
    made = []

    def factory():
        made.append(FakeSplitter())
        return made[-1]
    deps = make_deps(FakeLLM(['A [1].']), splitter_factory=factory)
    post_stream(deps)
    post_stream(deps)
    assert len(made) == 2 and made[0] is not made[1]


# --- AC-11: đường đi không qua LLM tổng hợp như v1 -------------------------------------------------

def test_ut26_ac11_emergency_is_one_v1_delta_without_retrieval(pipeline, monkeypatch):
    monkeypatch.setattr(main.rag, 'retrieve', lambda *a, **k: pytest.fail('must not retrieve'))
    events = post_stream(make_deps(FakeLLM([])), question='Tôi đau ngực dữ dội, khó thở')
    assert [e['type'] for e in events] == ['delta', 'done']
    assert '115' in events[0]['text']
    assert events[-1]['trace'][-1] == 'Response Agent (Safety Directive)'
    assert not number_check(events)


def test_ut27_ac11_greeting_is_one_v1_delta(pipeline, monkeypatch):
    monkeypatch.setattr(main.rag, 'retrieve', lambda *a, **k: pytest.fail('must not retrieve'))
    events = post_stream(make_deps(FakeLLM([])), question='Xin chào')
    assert [e['type'] for e in events] == ['delta', 'done']
    assert events[-1]['trace'] == ['Coordinator', 'Rule Agent', 'Rule Agent (Approved)', 'Conversation Agent']


def test_ut28_ac11_no_source_streams_the_refusal_unchecked_like_v1(pipeline):
    pipeline['sources'] = []
    guard = FakeGuard()
    llm = FakeLLM([REFUSAL])
    events = post_stream(make_deps(llm, guard), question='Cách làm món phở bò ngon tại nhà?')
    assert ''.join(deltas(events)) == REFUSAL
    assert guard.checked == []
    assert events[-1]['trace'][-3:] == ['Knowledge Agent (Retrieved 0 sources)',
                                        'Knowledge Graph Agent (Skipped: no relevant source)', 'Response Agent (No source)']
    assert llm.calls[0]['include_tail'] is True


def test_ut29_ac11_only_unreviewed_sources_are_streamed_unchecked(pipeline):
    pipeline['sources'] = [WEB]
    guard = FakeGuard()
    events = post_stream(make_deps(FakeLLM(['Đã tìm thấy các nguồn tham khảo [1]. ', 'Mở 77 nguồn.']), guard))
    assert guard.checked == []                                                # ctx None → skipped, như v1
    assert 'Response Agent (Links to unreviewed sources)' in events[-1]['trace']
    assert not number_check(events)


# Test List REQ-DA-03-T2 (UT ↔ nguồn):
# UT-1..UT-4  AC-7 (UT-4: câu chỉ khoảng trắng gộp vào câu kế, §5.2 bước 4)
# UT-5..UT-9  AC-8; UT-8 cũng EC-20; UT-9 NFR-10
# UT-10, UT-11 EC-16 · UT-12, UT-13 AC-9 · UT-14..UT-16 NFR-7 (chuỗi trace §5.3)
# UT-17 AC-10, EC-18 · UT-18..UT-20 NFR-8 · UT-21..UT-23 EC-17 · UT-24, UT-25 EC-19
# UT-26..UT-29 AC-11
# Chưa đo: NFR-1, NFR-2 (cần T1 thật + runner T3, đo trên server).
