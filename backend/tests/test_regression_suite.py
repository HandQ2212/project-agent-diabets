"""Bộ regression nội dung (REQ-DA-03-T3): cấu trúc AC-12/AC-13 + hàm chấm thuần, không cần dịch vụ."""
import json
from collections import Counter
from pathlib import Path

import pytest

from backend.app.rag import issuer_of
from ml import run_answer_regression as rr

ROOT = Path(__file__).resolve().parents[2]
KB = {d['id']: d for d in json.loads((ROOT / 'knowledge/sources_v2.json').read_text(encoding='utf-8'))}
ALL_IDS = set(KB)
for extra in ('sources.json', 'web_sources.json'):
    p = ROOT / 'knowledge' / extra
    if p.exists():
        data = json.loads(p.read_text(encoding='utf-8'))
        ALL_IDS |= {d['id'] for d in (data if isinstance(data, list) else data.get('sources', [])) if 'id' in d}
SUITE = rr.load_suite(ROOT / 'knowledge/answer_regression.json')
EVAL = json.loads((ROOT / 'knowledge/eval_questions.json').read_text(encoding='utf-8'))


def test_ut18_ac13_group_sizes():
    n = Counter(c['group'] for c in SUITE['cases'])
    assert n['fabricated_normal'] >= 4 and n['leading_number'] >= 4 and n['conversion'] >= 3
    assert n['accent_pair'] >= 4 and n['ada_vs_byt'] >= 4
    qs = ' '.join(c['q'] for c in SUITE['cases'])
    assert '70–99' in qs and 'HbA1c dưới 6%' in qs and '250 mg/dL' in qs


def test_ut19_ac13_every_required_value_is_in_its_source():
    for c in SUITE['cases']:
        for exp in c['must_include']:
            assert exp['source_id'] in KB, (c['id'], exp['source_id'])
            assert rr.norm(exp['value']) in rr.norm(KB[exp['source_id']]['text']), (c['id'], exp['value'])


def test_ut20_ac13_pairs_inherit_criteria():
    by_id = {c['id']: c for c in SUITE['cases']}
    for c in SUITE['cases']:
        if c['group'] == 'accent_pair':
            base = by_id[c['pair_of']]
            assert c['must_include'] == base['must_include'] and c['must_not_include'] == base['must_not_include']


@pytest.mark.parametrize('topic,words', [('tuổi sàng lọc', ('sàng lọc', 'sang loc')),
                                         ('huyết áp', ('huyết áp mục tiêu', 'huyet ap muc tieu')),
                                         ('LDL', ('ldl',)), ('rượu', ('rượu', 'ruou'))])
def test_ut21_ac12_ada_and_byt_with_and_without_accents(topic, words):
    qs = [x for x in EVAL['in_domain'] if any(w in x['q'].lower() for w in words)]
    accented = [x for x in qs if x['q'] != rr.norm(x['q']).encode('ascii', 'ignore').decode()]
    plain = [x for x in qs if x['q'].isascii()]
    assert accented and plain, topic
    for x in accented + plain:
        issuers = {issuer_of(KB[i]['url']) for i in x['relevant'] if i in KB}
        assert any('ADA' in s for s in issuers) and any('Bộ Y tế' in s for s in issuers), (topic, x['q'])


def test_ut22_ac12_every_relevant_id_exists():
    missing = {i for x in EVAL['in_domain'] for i in x['relevant'] if i not in ALL_IDS}
    assert not missing


CASE = {'must_include': [{'any': ['130/80'], 'near': ['ADA'], 'window': 20}],
        'must_not_include': ['70-99'], 'number_check_allowed': ['passed'], 'min_reviewed_sources': 1}


def test_ut23_evaluate():
    assert rr.evaluate(CASE, 'Theo ADA: dưới 130/80 [1].', 'passed', 2) == []
    assert rr.evaluate(CASE, 'Theo ADA: ' + 'x' * 40 + ' 130/80', 'passed', 2)[0].startswith('"130/80" không đứng gần')
    f = rr.evaluate(CASE, 'ADA 130/80; bình thường 70 – 99', 'blocked', 0)
    assert len(f) == 3 and 'có cụm cấm: 70-99' in f


def test_ut24_norm_decimal_and_dash():
    assert rr.norm('5.6 — 6.9  mmol') == '5,6-6,9 mmol'


def test_ut25_run_counts_pass_only_when_all_runs_pass_and_service_error_fails():
    suite = {'cases': [dict(CASE, id='A', group='ada_vs_byt', q='q')]}
    answers = iter(['Theo ADA 130/80', 'Theo ADA 130/80', None])

    def asker(_url, _q):
        a = next(answers)
        if a is None:
            raise ConnectionError('down')
        return {'answer': a, 'number_check': 'passed', 'reviewed_sources': 2, 't_first_delta_s': 1.0, 't_done_s': 2.0}
    report = rr.run(suite, 'http://x', 3, None, None, asker=asker)
    c = report['cases'][0]
    assert c['passed_runs'] == 2 and c['verdict'] == 'FAIL' and c['runs'][2]['service_error']
    assert report['started_at'].endswith('+07:00') and report['ttft_s']['n'] == 2


def test_ut26_refutation_of_a_leading_number_is_not_a_violation():
    case = {'must_not_include': ['70-99'], 'allow_refutation': True}
    assert rr.evaluate(case, 'Không, bình thường không phải là 70–99 mg/dL. Mức đúng là 99 hoặc thấp hơn.', None, 1) == []
    assert rr.evaluate(case, 'Đúng vậy, bình thường là 70–99 mg/dL.', None, 1) == ['có cụm cấm: 70-99']
    assert rr.evaluate({'must_not_include': ['70-99']}, 'Không lo, bình thường 70–99.', None, 1) == ['có cụm cấm: 70-99']
