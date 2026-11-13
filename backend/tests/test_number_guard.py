"""Hậu kiểm số y khoa (DEF-BE-4): không số nào ngoài nguồn được tới người dùng."""
import json

import pytest
from fastapi.testclient import TestClient

from backend.app import main, number_guard as ng, rag

CTX = ['Glucose lúc đói 100–125 mg/dL (5,6–6,9 mmol/L) là tiền đái tháo đường; HbA1c 5,7–6,4%. Bình thường dưới 1.000 đơn vị. 99 mg/dL hoặc thấp hơn.']


def test_numbers_present_in_context_pass():
    assert ng.find_unsupported('Tiền đái tháo đường khi glucose đói 100–125 mg/dL [1].', *CTX) == []


def test_invented_numbers_are_flagged():
    assert ng.find_unsupported('Bình thường là 70–99 mg/dL (3,9–5,5 mmol/L) [1].', *CTX) == ['70', '3,9', '5,5']


@pytest.mark.parametrize('answer', ['khoảng 5.6 mmol/L', 'khoảng 5,6 mmol/L'])
def test_decimal_comma_and_dot_are_the_same_number(answer):
    assert ng.find_unsupported(answer, *CTX) == []
    assert ng.find_unsupported(answer.replace('5', '7'), *CTX) != []


def test_thousand_separator_is_normalised():
    assert ng.find_unsupported('1000 đơn vị', *CTX) == []


def test_range_checks_both_ends():
    assert ng.find_unsupported('5,7–6,4%', *CTX) == []
    assert ng.find_unsupported('5,7–6,9%', *CTX) == []
    assert ng.find_unsupported('5,7–6,5%', *CTX) == ['6,5']


def test_citations_list_numbers_and_identifiers_are_ignored():
    text = '1. HbA1c cao [3].\n- 2) Xem dc26-S005 và PMC12690188.'
    assert ng.find_unsupported(text, 'HbA1c') == []


def test_number_in_a_refusal_sentence_is_still_flagged_but_plain_refusal_passes():
    assert ng.find_unsupported('Tài liệu chưa đề cập nội dung này.', *CTX) == []
    assert 70.0 in {v for _, v in ng.extract_numbers('Thường 70–99 mg/dL, tuy nhiên tài liệu không cung cấp.')}
    assert ng.find_unsupported('Thường 70–99 mg/dL, tuy nhiên tài liệu không cung cấp.', 'Glucose 99 mg/dL') == ['70']


def test_number_in_question_is_allowed():
    assert ng.find_unsupported('HbA1c 6,8% là mức đo của bạn.', 'HbA1c 6.8 có nguy hiểm không') == []


SOURCES = [{'title': 'Nguồn ADA', 'url': 'https://example.org/a', 'topic': 't', 'text': CTX[0]}]


def _fake_parts(responses):
    calls = []

    def parts(question, sources, history=None, forbidden_numbers=None, **kwargs):
        calls.append(forbidden_numbers)
        yield responses[min(len(calls) - 1, len(responses) - 1)]
    return parts, calls


def test_guard_passes_clean_answer_without_regeneration(monkeypatch):
    parts, calls = _fake_parts(['Tiền đái tháo đường: 100–125 mg/dL [1].'])
    monkeypatch.setattr(rag, 'answer_parts', parts)
    result = rag.guard_answer('q', SOURCES)
    assert result.check['status'] == 'passed' and len(calls) == 1


def test_guard_regenerates_once_with_forbidden_numbers(monkeypatch):
    parts, calls = _fake_parts(['Bình thường 70–99 mg/dL [1].', 'Bình thường: 99 mg/dL hoặc thấp hơn [1].'])
    monkeypatch.setattr(rag, 'answer_parts', parts)
    result = rag.guard_answer('q', SOURCES)
    assert result.check['status'] == 'regenerated' and calls == [None, ['70–99']]
    assert '70' not in result


def test_guard_blocks_after_second_violation(monkeypatch):
    parts, calls = _fake_parts(['Bình thường 70–99 mg/dL [1].'])
    monkeypatch.setattr(rag, 'answer_parts', parts)
    result = rag.guard_answer('q', SOURCES)
    assert result.check['status'] == 'blocked' and len(calls) == 2
    assert '70' not in result and '[1] Nguồn ADA' in result


def test_guard_skips_when_only_unreviewed_web_sources(monkeypatch):
    parts, calls = _fake_parts(['Đã tìm thấy [1] 70.'])
    monkeypatch.setattr(rag, 'answer_parts', parts)
    web = [dict(SOURCES[0], review_status='unreviewed_web')]
    assert rag.guard_answer('q', web).check['status'] == 'skipped'


def test_chat_endpoint_adds_number_check_trace(monkeypatch):
    client = TestClient(main.app)
    monkeypatch.setattr(main.rag, 'standalone_question', lambda q, h: q)
    monkeypatch.setattr(main.rag, 'retrieve', lambda *a, **k: list(SOURCES))
    monkeypatch.setattr(main.knowledge_graph, 'lookup', lambda *a, **k: None)
    parts, _ = _fake_parts(['Bình thường 70–99 mg/dL [1].'])
    monkeypatch.setattr(rag, 'answer_parts', parts)
    body = client.post('/api/chat', json={'question': 'Đường huyết đói bình thường?'}).json()
    assert '70' not in body['answer']
    assert any(t.startswith('Response Agent (Number check: blocked') for t in body['trace'])


def test_stream_never_sends_unchecked_numbers(monkeypatch):
    client = TestClient(main.app)
    monkeypatch.setattr(main.rag, 'standalone_question', lambda q, h: q)
    monkeypatch.setattr(main.rag, 'retrieve', lambda *a, **k: list(SOURCES))
    monkeypatch.setattr(main.knowledge_graph, 'lookup', lambda *a, **k: None)
    parts, _ = _fake_parts(['Bình thường 70–99 mg/dL [1].'])
    monkeypatch.setattr(rag, 'answer_parts', parts)
    response = client.post('/api/chat/stream', json={'question': 'Đường huyết đói bình thường?'})
    events = [json.loads(line) for line in response.text.splitlines()]
    text = ''.join(e['text'] for e in events if e['type'] == 'delta')
    assert '70' not in text and any('Number check: blocked' in t for t in events[-1]['trace'])


# ---------------------------------------------------------------- guard v2 (REQ-DA-03-T1, design-data §4)

V2_SRC = [{'title': 'Đổi đơn vị', 'url': 'https://example.org/u', 'topic': 't',
           'text': 'Glucose mmol/L = mg/dL chia 18. Glucose lúc đói 100–125 mg/dL là tiền đái tháo đường; '
                   '99 mg/dL hoặc thấp hơn là bình thường. HbA1c từ 6,5% trở lên là đái tháo đường. '
                   'Ví dụ 70 mg/dL.'}]


def _v2(answer, question='q', sources=V2_SRC, history=None):
    ctx = ng.GuardContext.for_turn(question, sources, history)
    return ng.NumberGuard().check(answer, ctx)


@pytest.mark.parametrize('answer', ['250 mg/dL ÷ 18 ≈ 13,9 mmol/L', '250 mg/dL = 13,89 mmol/L', '250 mg/dL khoảng 14 mmol/L'])
def test_ut1_ac1_conversion_of_user_value_is_accepted(answer):
    assert _v2(answer, 'Đường huyết tôi 250 mg/dL, đổi ra mmol/L?').ok


@pytest.mark.parametrize('answer', ['13,8 mmol/L', '13,88 mmol/L', '13 mmol/L'])
def test_ut2_ac1_wrong_rounding_is_rejected(answer):
    v = _v2(answer, 'Đường huyết tôi 250 mg/dL')
    assert not v.ok and v.unsupported == (answer.split()[0],)


def test_ut3b_conversion_needs_its_base_in_the_same_text():
    # 99/18 ≈ 6 nhưng 99 không được nêu → "dưới 6%" không được coi là số quy đổi.
    assert _v2('Bình thường là dưới 6 [1].').unsupported == ('6',)
    assert _v2('99 mg/dL hoặc thấp hơn, tức khoảng 5,5 mmol/L hoặc thấp hơn [1].').ok
    assert _v2('13,9 mmol/L', 'tôi 250 mg/dL').unsupported == ('13,9',)


def test_ut3_ac1_no_factor_in_sources_means_no_conversion():
    src = [{'title': 'x', 'url': 'u', 'text': 'Glucose 126 mg/dL.'}]
    assert _v2('250 mg/dL là 13,9 mmol/L', 'tôi 250 mg/dL', src).unsupported == ('13,9',)


def test_ut4_ac2_user_value_may_be_repeated_as_plain():
    assert _v2('Mức 6,8% bạn nêu cao hơn ngưỡng 6,5% [1].', 'HbA1c tôi 6,8% có sao không').ok


def test_ut5_ac3_leading_number_cannot_be_a_threshold():
    v = _v2('Bình thường là dưới 6% [1].', 'Có phải HbA1c dưới 6% là bình thường không?')
    assert v.unsupported == ('6',)
    assert _v2('Ngưỡng 6,5% trở lên [1].', 'HbA1c 6,5 thì sao').ok   # 6,5 có trong nguồn


def test_ut6_ac4_range_needs_the_pair_in_sources():
    # 70 và 99 đều có trong nguồn nhưng ở hai chỗ khác nhau: khoảng 70–99 không có → vi phạm cả cụm.
    assert _v2('Bình thường 70–99 mg/dL [1].').unsupported == ('70–99',)
    assert _v2('Có phải 70–99 không?', 'Có phải bình thường 70–99 không?', ).unsupported == ('70–99',)
    assert _v2('Tiền ĐTĐ: 100–125 mg/dL [1].').ok
    assert _v2('từ 100 đến 125 mg/dL').ok
    assert _v2('125–100 mg/dL').unsupported == ('125–100',)


def test_ut7_ac4_converted_range_is_accepted():
    assert _v2('100–125 mg/dL tương đương 5,6–6,9 mmol/L').ok
    assert _v2('5,6–7,0 mmol/L').unsupported == ('5,6–7,0',)


def test_ut8_ac5_v1_rules_still_hold():
    assert _v2('1. Có 2 lần [1]. Xem dc26-S005 và PMC12690188.').ok
    assert _v2('Khoảng 99,0 mg/dL').ok        # 99 = 99,0
    assert _v2('Glucose 1.000').unsupported == ('1.000',)


def test_ut9_roles():
    mentions, _ = ng.parse('dưới 6%, mức 6% bạn nêu, từ 6,5% trở lên, 70–99, 250 = 13,9')
    roles = [m.role.name for m in mentions]
    assert roles == ['THRESHOLD', 'PLAIN', 'THRESHOLD', 'RANGE_END', 'RANGE_END', 'PLAIN', 'PLAIN']


def test_ut10_for_turn_none_without_reviewed_sources():
    assert ng.GuardContext.for_turn('q', [dict(V2_SRC[0], review_status='unreviewed_web')]) is None
    ctx = ng.GuardContext.for_turn('q', V2_SRC, [{'role': 'user', 'content': 'tôi 140'}, {'role': 'assistant', 'content': '555'}])
    assert 140.0 in ctx.user_values and 555.0 not in ctx.user_values and ctx.factors == (18.0,)


def test_ut11_ac6_chat_and_stream_give_the_same_verdict(monkeypatch):
    client = TestClient(main.app)
    monkeypatch.setattr(main.rag, 'standalone_question', lambda q, h: q)
    monkeypatch.setattr(main.rag, 'retrieve', lambda *a, **k: list(V2_SRC))
    monkeypatch.setattr(main.knowledge_graph, 'lookup', lambda *a, **k: None)
    parts, _ = _fake_parts(['250 mg/dL ÷ 18 ≈ 13,9 mmol/L [1]. '])
    monkeypatch.setattr(rag, 'answer_parts', parts)
    q = {'question': 'Đường huyết tôi 250 mg/dL đổi ra mmol/L?'}
    chat = client.post('/api/chat', json=q).json()
    events = [json.loads(line) for line in client.post('/api/chat/stream', json=q).text.splitlines()]
    assert any('Number check: passed' in t for t in chat['trace'])
    assert any('Number check: passed' in t for t in events[-1]['trace'])
    assert '13,9' in chat['answer'] and '13,9' in ''.join(e['text'] for e in events if e['type'] == 'delta')
