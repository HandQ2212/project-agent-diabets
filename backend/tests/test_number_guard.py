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

    def parts(question, sources, history=None, forbidden_numbers=None):
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
    assert result.check['status'] == 'regenerated' and calls == [None, ['70']]
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
