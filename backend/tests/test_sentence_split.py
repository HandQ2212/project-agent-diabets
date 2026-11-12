"""SentenceSplitter (REQ-DA-03-T1, design-data §3.2)."""
import random

import pytest

from backend.app.sentence_split import MAX_SENTENCE_CHARS, SentenceSplitter

TEXT = ('Glucose lúc đói 100–125 mg/dL là tiền ĐTĐ [1]. HbA1c 5,7–6,4% [2]!\n\n'
        '1. Theo ADA: mục tiêu 130/80 [1].\n- Theo Bộ Y tế: 140/90 [2]. Hết')


def _run(tokens):
    s = SentenceSplitter()
    out = [c for t in tokens for c in s.feed(t)]
    return out + s.flush()


def test_ut12_join_invariant_any_tokenisation():
    rng = random.Random(7)
    for _ in range(50):
        cuts = sorted(rng.sample(range(1, len(TEXT)), 15))
        tokens = [TEXT[a:b] for a, b in zip([0] + cuts, cuts + [len(TEXT)])]
        out = _run(tokens)
        assert ''.join(out) == TEXT
        assert out == _run([TEXT])


def test_ut13_sentences():
    assert _run([TEXT]) == ['Glucose lúc đói 100–125 mg/dL là tiền ĐTĐ [1]. ', 'HbA1c 5,7–6,4% [2]!\n\n',
                            '1. Theo ADA: mục tiêu 130/80 [1].\n', '- Theo Bộ Y tế: 140/90 [2]. ', 'Hết']


def test_ut14_decimal_split_across_tokens_is_not_a_boundary():
    s = SentenceSplitter()
    assert s.feed('Mức 5.') == [] and s.feed('6 mmol/L. ') == [] and s.feed('Tiếp') == ['Mức 5.6 mmol/L. ']


def test_ut15_sentence_released_only_after_next_visible_char():
    s = SentenceSplitter()
    assert s.feed('Câu một. ') == []
    assert s.feed('C') == ['Câu một. ']


@pytest.mark.parametrize('n', [MAX_SENTENCE_CHARS + 50, 3 * MAX_SENTENCE_CHARS])
def test_ut16_long_run_without_punctuation_is_cut(n):
    text = ('chữ ' * n)[:n]
    out = _run([text])
    assert ''.join(out) == text and all(len(c) <= MAX_SENTENCE_CHARS for c in out)


def test_ut17_flush_empty():
    assert SentenceSplitter().flush() == []
