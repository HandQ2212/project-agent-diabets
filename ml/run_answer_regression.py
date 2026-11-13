"""Chạy bộ regression nội dung câu trả lời qua /api/chat/stream (REQ-DA-03-T3, design-data §7).

python -m ml.run_answer_regression [--runs 3] [--base-url http://127.0.0.1:8001] [--group G ...] [--case RG-01 ...]
                                   [--out artifacts/answer_regression] [--suite knowledge/answer_regression.json]

Mã thoát: 0 mọi case PASS; 1 có case FAIL; 2 lỗi cấu hình (file sai schema, không kết nối được ở lần đầu).
Mỗi lần chạy ghi t_first_delta_s (tới delta đầu có chữ) và t_done_s → dùng cho NFR-1/NFR-2.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import subprocess
import sys
import time
import unicodedata
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

VN = ZoneInfo('Asia/Ho_Chi_Minh')
GROUPS = ('fabricated_normal', 'leading_number', 'conversion', 'accent_pair', 'ada_vs_byt')
_NUMBER_CHECK = re.compile(r'Number check: (\w+)')


class SuiteError(ValueError):
    pass


def norm(text: str) -> str:
    """NFC, chữ thường, gộp khoảng trắng, mọi gạch → '-' không khoảng trắng quanh, '.' thập phân → ','."""
    t = unicodedata.normalize('NFC', text).lower()
    t = re.sub(r'\s+', ' ', t)
    t = re.sub(r'\s*[–—-]\s*', '-', t)
    return re.sub(r'(?<=\d)\.(?=\d)', ',', t)


def load_suite(path: str | Path) -> dict:
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(data, dict) or not isinstance(data.get('cases'), list):
        raise SuiteError('suite must be an object with a "cases" list')
    by_id = {}
    for c in data['cases']:
        if not {'id', 'group', 'q'} <= c.keys() or c['group'] not in GROUPS:
            raise SuiteError(f'bad case {c.get("id")}')
        if c['id'] in by_id:
            raise SuiteError(f'duplicate id {c["id"]}')
        by_id[c['id']] = c
    for c in data['cases']:
        if 'inherit' in c:
            base = by_id.get(c['inherit'])
            if base is None or 'inherit' in base:
                raise SuiteError(f'{c["id"]}: bad inherit')
            for key in ('must_include', 'must_not_include', 'number_check_allowed', 'min_reviewed_sources'):
                c.setdefault(key, base.get(key))
        for key, default in (('must_include', []), ('must_not_include', []),
                             ('number_check_allowed', ['passed', 'regenerated', 'filtered']), ('min_reviewed_sources', 1)):
            if c.get(key) is None:
                c[key] = default
    return data


_NEGATION = re.compile(r'(?<!\w)(?:không|chưa|sai)(?!\w)')


def _sentences_with(a: str, needle: str) -> list[str]:
    """Các câu (đã chuẩn hoá) chứa needle. Câu mớm số được nhắc lại để bác bỏ ("không phải 70-99") nằm trong
    câu có từ phủ định; case có allow_refutation=true thì câu đó không tính là vi phạm."""
    return [s for s in re.split(r'(?<=[.!?])\s+|\n+', a) if needle in s]


def _near_ok(answer: str, start: int, end: int, near: list[str], window: int) -> bool:
    lo, hi = max(0, start - window), min(len(answer), end + window)
    span = answer[lo:hi]
    return any(norm(n) in span for n in near)


def evaluate(case: dict, answer: str, number_check: str | None, reviewed_sources: int) -> list[str]:
    """Hàm chấm thuần: trả danh sách lỗi (rỗng = đạt)."""
    failures = []
    a = norm(answer)
    for exp in case.get('must_include', []):
        hits = [(m.start(), m.end()) for alt in exp['any'] for m in re.finditer(re.escape(norm(alt)), a)]
        if not hits:
            failures.append(f'thiếu: {" | ".join(exp["any"])}')
        elif exp.get('near') and not any(_near_ok(a, s, e, exp['near'], exp.get('window', 160)) for s, e in hits):
            failures.append(f'"{exp["any"][0]}" không đứng gần {exp["near"]}')
    for bad in case.get('must_not_include', []):
        if any(not (case.get('allow_refutation') and _NEGATION.search(sent)) for sent in _sentences_with(a, norm(bad))):
            failures.append(f'có cụm cấm: {bad}')
    allowed = case.get('number_check_allowed', [])
    if allowed and number_check not in allowed:
        failures.append(f'hậu kiểm {number_check} ∉ {allowed}')
    if reviewed_sources < case.get('min_reviewed_sources', 0):
        failures.append(f'chỉ {reviewed_sources} nguồn đã duyệt < {case["min_reviewed_sources"]}')
    return failures


def ask(base_url: str, question: str, timeout: float = 180.0) -> dict:
    import httpx
    t0 = time.monotonic()
    first = None
    text, final = [], None
    with httpx.stream('POST', f'{base_url}/api/chat/stream', json={'question': question}, timeout=timeout) as r:
        r.raise_for_status()
        for line in r.iter_lines():
            if not line:
                continue
            ev = json.loads(line)
            if ev.get('type') == 'delta' and ev.get('text'):
                if first is None and ev['text'].strip():
                    first = time.monotonic() - t0
                text.append(ev['text'])
            elif ev.get('type') == 'error':
                raise RuntimeError(ev.get('message') or 'stream error')
            elif ev.get('type') == 'done':
                final = ev
    if final is None:
        raise RuntimeError('stream ended without done')
    trace = final.get('trace') or []
    m = next((_NUMBER_CHECK.search(t) for t in trace if _NUMBER_CHECK.search(t)), None)
    sources = final.get('sources') or []
    reviewed = sum(1 for s in sources if s.get('review_status') != 'unreviewed_web')
    return {'answer': ''.join(text), 'number_check': m.group(1) if m else None, 'reviewed_sources': reviewed,
            't_first_delta_s': round(first, 2) if first is not None else None,
            't_done_s': round(time.monotonic() - t0, 2)}


def _commit() -> str:
    try:
        return subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], capture_output=True, text=True,
                              check=True).stdout.strip()
    except Exception:
        return 'unknown'


def _pct(values: list[float], p: float) -> float | None:
    if not values:
        return None
    s = sorted(values)
    k = max(0, min(len(s) - 1, round(p * (len(s) - 1))))
    return s[k]


def run(suite: dict, base_url: str, runs: int, groups: list[str] | None, ids: list[str] | None,
        asker=ask) -> dict:
    cases = [c for c in suite['cases'] if (not groups or c['group'] in groups) and (not ids or c['id'] in ids)]
    out_cases, ttft, done = [], [], []
    for c in cases:
        results = []
        for i in range(1, runs + 1):
            try:
                r = asker(base_url, c['q'])
                r.update(run=i, failures=evaluate(c, r['answer'], r['number_check'], r['reviewed_sources']),
                         service_error=False)
                if r['t_first_delta_s'] is not None:
                    ttft.append(r['t_first_delta_s'])
                done.append(r['t_done_s'])
            except Exception as exc:  # EC-21: lỗi dịch vụ tính là không đạt
                r = {'run': i, 'answer': '', 'number_check': None, 'reviewed_sources': 0, 't_first_delta_s': None,
                     't_done_s': None, 'failures': [f'lỗi dịch vụ: {type(exc).__name__}: {exc}'], 'service_error': True}
            results.append(r)
            print(f"{c['id']} run {i}: {'OK' if not r['failures'] else '; '.join(r['failures'])}", file=sys.stderr)
        passed = sum(1 for r in results if not r['failures'])
        out_cases.append({'id': c['id'], 'group': c['group'], 'q': c['q'], 'passed_runs': passed,
                          'verdict': 'PASS' if passed == runs else 'FAIL', 'runs': results})
    by_group: dict = {}
    for c in out_cases:
        g = by_group.setdefault(c['group'], {'cases': 0, 'passed': 0})
        g['cases'] += 1
        g['passed'] += c['verdict'] == 'PASS'
    return {
        'started_at': datetime.now(VN).isoformat(timespec='seconds'),
        'commit': _commit(), 'model': os.getenv('OLLAMA_MODEL', 'qwen3:4b-instruct'),
        'base_url': base_url, 'runs': runs,
        'summary': {'cases': len(out_cases), 'passed': sum(c['verdict'] == 'PASS' for c in out_cases), 'by_group': by_group},
        'ttft_s': {'p50': statistics.median(ttft) if ttft else None, 'p95': _pct(ttft, 0.95), 'n': len(ttft)},
        'done_s': {'p50': statistics.median(done) if done else None, 'n': len(done)},
        'cases': out_cases,
    }


def to_markdown(report: dict) -> str:
    s, t = report['summary'], report['ttft_s']
    lines = [f"# Regression câu trả lời – {report['started_at']}", '',
             f"commit `{report['commit']}` · model `{report['model']}` · {report['base_url']} · R = {report['runs']}", '',
             f"**{s['passed']}/{s['cases']} case PASS** · chữ đầu p50 = {t['p50']} s, p95 = {t['p95']} s (n = {t['n']})"
             f" · done p50 = {report['done_s']['p50']} s", '',
             '| id | nhóm | đạt/R | lỗi đầu tiên |', '|---|---|---|---|']
    for c in report['cases']:
        first = next((f for r in c['runs'] for f in r['failures']), '')
        lines.append(f"| {c['id']} | {c['group']} | {c['passed_runs']}/{report['runs']} | {first.replace('|', '/')} |")
    return '\n'.join(lines) + '\n'


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--runs', type=int)
    ap.add_argument('--base-url', default='http://127.0.0.1:8001')
    ap.add_argument('--group', nargs='*', choices=GROUPS)
    ap.add_argument('--case', nargs='*')
    ap.add_argument('--out', default='artifacts/answer_regression')
    ap.add_argument('--suite', default='knowledge/answer_regression.json')
    args = ap.parse_args(argv)
    try:
        suite = load_suite(args.suite)
        import httpx
        httpx.get(f'{args.base_url}/api/health', timeout=5)
    except (SuiteError, OSError, json.JSONDecodeError) as exc:
        print(f'config error: {exc}', file=sys.stderr)
        return 2
    except Exception as exc:
        print(f'cannot reach {args.base_url}: {exc}', file=sys.stderr)
        return 2
    report = run(suite, args.base_url, args.runs or suite.get('runs', 3), args.group, args.case)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(VN).strftime('%Y%m%dT%H%M%S%z')
    (out / f'{stamp}.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    (out / f'{stamp}.md').write_text(to_markdown(report), encoding='utf-8')
    print(to_markdown(report))
    return 0 if report['summary']['passed'] == report['summary']['cases'] else 1


if __name__ == '__main__':
    sys.exit(main())
