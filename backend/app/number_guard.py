"""Hậu kiểm tất định: mọi con số trong câu trả lời phải được nguồn đã duyệt hỗ trợ.

Model nhỏ hay "nhớ" các ngưỡng y khoa từ dữ liệu huấn luyện (ví dụ 70–99 mg/dL) dù không có trong nguồn.
Mô-đun này không gọi LLM, không I/O.

v1 (`find_unsupported`): mỗi số phải xuất hiện nguyên văn trong ngữ cảnh (giữ để tương thích).
v2 (`NumberGuard`, REQ-DA-03, design-data §4): phân vai số (PLAIN / THRESHOLD / RANGE_END), khoảng phải có
nguyên cặp trong nguồn, chấp nhận số quy đổi một bước bằng hệ số có trong nguồn, số chỉ có trong câu hỏi
chỉ được nhắc lại như số đo của người dùng chứ không được dùng làm ngưỡng.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum

# Số đứng riêng: không dính chữ (HbA1c, PMC123, dc26-S005 bị loại), cho phép "1.000" (hàng nghìn) và "5,6" / "5.6".
_NUMBER = re.compile(r'(?<![\w])(\d{1,3}(?:\.\d{3})+(?!\d)|\d+(?:[.,]\d+)?)')
_CITATION = re.compile(r'\[\d+\]')
_LIST_MARK = re.compile(r'(?m)^\s*(?:[-*•]\s*)?\d{1,2}[.)]\s+')
# Số đếm rất nhỏ (0–2) xuất hiện tự nhiên trong lời văn; mọi số khác phải có trong nguồn.
EXEMPT = {0.0, 1.0, 2.0}
KNOWN_FACTORS = (18.0, 38.7, 88.6)  # glucose mg/dL↔mmol/L, cholesterol, triglyceride

REMOVED_NOTE = ('Một phần nội dung có con số chưa được nguồn xác nhận nên đã được lược bỏ; '
                'vui lòng xem nguồn bên dưới.')


def normalize(raw: str) -> float:
    """'5,6' và '5.6' -> 5.6; '1.000' -> 1000.0."""
    if re.fullmatch(r'\d{1,3}(?:\.\d{3})+', raw):
        raw = raw.replace('.', '')
    return round(float(raw.replace(',', '.')), 6)


def _decimals(raw: str) -> int:
    if re.fullmatch(r'\d{1,3}(?:\.\d{3})+', raw):
        return 0
    m = re.search(r'[.,](\d+)$', raw)
    return len(m.group(1)) if m else 0


def _blank(match: re.Match) -> str:
    return ' ' * len(match.group(0))


def _clean(text: str) -> str:
    """Xoá [n] và số thứ tự đầu dòng nhưng giữ nguyên vị trí ký tự."""
    return _LIST_MARK.sub(_blank, _CITATION.sub(_blank, unicodedata.normalize('NFC', text)))


def extract_numbers(text: str) -> list[tuple[str, float]]:
    return [(m.group(1), normalize(m.group(1))) for m in _NUMBER.finditer(_clean(text))]


def allowed_values(*texts: str) -> set[float]:
    values: set[float] = set()
    for text in texts:
        values.update(value for _, value in extract_numbers(text))
    return values


def find_unsupported(answer: str, *context: str) -> list[str]:
    """v1: các số (nguyên văn, không trùng) trong answer mà không có trong context. Mọi context coi là nguồn."""
    allowed = allowed_values(*context) | EXEMPT
    seen, bad = set(), []
    for raw, value in extract_numbers(answer):
        if value not in allowed and value not in seen:
            seen.add(value)
            bad.append(raw)
    return bad


# ---------------------------------------------------------------- v2

class NumberRole(Enum):
    PLAIN = 'plain'          # số đứng một mình (nhắc lại số đo, số đếm, giá trị quy đổi)
    THRESHOLD = 'threshold'  # số đi với dấu hiệu ngưỡng (design §4.2)
    RANGE_END = 'range_end'  # đầu mút của khoảng a–b


@dataclass(frozen=True)
class NumberMention:
    raw: str
    value: float
    decimals: int
    role: NumberRole
    start: int
    end: int


@dataclass(frozen=True)
class RangeMention:
    low: NumberMention
    high: NumberMention
    raw: str


@dataclass(frozen=True)
class GuardVerdict:
    ok: bool
    unsupported: tuple[str, ...]


_RANGE_JOIN = re.compile(r'\s*(?:[–—-]|đến)\s*', re.IGNORECASE)
_CLAUSE_BREAK = frozenset(',;:()\n.!?')
_BEFORE_WORDS = ('dưới', 'trên', 'từ', 'tối thiểu', 'tối đa', 'ít nhất', 'không quá', 'vượt',
                 'bình thường', 'mục tiêu', 'ngưỡng')
_BEFORE_RE = re.compile(r'(?<!\w)(?:' + '|'.join(re.escape(w) for w in _BEFORE_WORDS) + r')(?!\w)', re.IGNORECASE)
_AFTER_RE = re.compile(r'^\s*(?:[^\s\d,;:()]+\s+){0,2}?(?:trở lên|trở xuống|hoặc thấp hơn|hoặc cao hơn)(?!\w)',
                       re.IGNORECASE)


def _inside(i: int, spans: list[tuple[int, int]]) -> bool:
    return any(s <= i < e for s, e in spans)


def _clause_start(text: str, pos: int, spans: list[tuple[int, int]]) -> int:
    for i in range(pos - 1, -1, -1):
        if text[i] in _CLAUSE_BREAK and not _inside(i, spans):
            return i + 1
    return 0


def _clause_end(text: str, pos: int, spans: list[tuple[int, int]]) -> int:
    for i in range(pos, len(text)):
        if text[i] in _CLAUSE_BREAK and not _inside(i, spans):
            return i
    return len(text)


def _is_threshold(text: str, start: int, end: int, spans: list[tuple[int, int]]) -> bool:
    before = text[_clause_start(text, start, spans):start]
    last3 = ' '.join(before.split()[-3:])
    if any(c in last3 for c in '<≤>≥') or _BEFORE_RE.search(last3):
        return True
    return bool(_AFTER_RE.match(text[end:_clause_end(text, end, spans)]))


def parse(text: str) -> tuple[list[NumberMention], list[RangeMention]]:
    """Trích số + gán vai trò. Trả (mọi mention theo thứ tự, các khoảng)."""
    cleaned = _clean(text)
    matches = list(_NUMBER.finditer(cleaned))
    spans = [m.span(1) for m in matches]
    in_range: set[int] = set()
    pairs: list[tuple[int, int]] = []
    i = 0
    while i < len(matches) - 1:
        if _RANGE_JOIN.fullmatch(cleaned[matches[i].end(1):matches[i + 1].start(1)]):
            pairs.append((i, i + 1))
            in_range.update((i, i + 1))
            i += 2
        else:
            i += 1
    mentions = []
    for k, m in enumerate(matches):
        raw = m.group(1)
        if k in in_range:
            role = NumberRole.RANGE_END
        elif _is_threshold(cleaned, m.start(1), m.end(1), spans):
            role = NumberRole.THRESHOLD
        else:
            role = NumberRole.PLAIN
        mentions.append(NumberMention(raw, normalize(raw), _decimals(raw), role, m.start(1), m.end(1)))
    ranges = [RangeMention(mentions[a], mentions[b], cleaned[mentions[a].start:mentions[b].end]) for a, b in pairs]
    return mentions, ranges


@dataclass(frozen=True)
class GuardContext:
    source_values: frozenset[float]
    source_ranges: frozenset[tuple[float, float]]
    user_values: frozenset[float]
    factors: tuple[float, ...]

    @staticmethod
    def from_texts(source_texts: list[str], user_texts: list[str]) -> 'GuardContext':
        values: set[float] = set()
        ranges: set[tuple[float, float]] = set()
        for text in source_texts:
            mentions, rngs = parse(text)
            values.update(m.value for m in mentions)
            ranges.update((r.low.value, r.high.value) for r in rngs)
        users: set[float] = set()
        for text in user_texts:
            users.update(m.value for m in parse(text)[0])
        factors = tuple(f for f in KNOWN_FACTORS if f in values)
        return GuardContext(frozenset(values), frozenset(ranges), frozenset(users), factors)

    @staticmethod
    def for_turn(question: str, sources: list[dict], history: list[dict] | None = None) -> 'GuardContext | None':
        """None khi không có nguồn đã duyệt (review_status != 'unreviewed_web') → bỏ kiểm (status 'skipped')."""
        reviewed = [s for s in sources if s.get('review_status') != 'unreviewed_web']
        if not reviewed:
            return None
        source_texts = [f"{s.get('title', '')} {s.get('url', '')} {s.get('text', '')}" for s in reviewed]
        user_texts = [question] + [m.get('content', '') for m in (history or []) if m.get('role') == 'user']
        return GuardContext.from_texts(source_texts, user_texts)


def _rounds_to(x: NumberMention, exact: Decimal) -> bool:
    """x == round_half_up(exact, số chữ số thập phân mà x được viết)."""
    q = Decimal(1).scaleb(-x.decimals)
    return exact.quantize(q, rounding=ROUND_HALF_UP) == Decimal(str(x.value)).quantize(q)


def _derived(x: NumberMention, base: frozenset[float], factors: tuple[float, ...]) -> bool:
    for v in base:
        dv = Decimal(str(v))
        for f in factors:
            df = Decimal(str(f))
            if _rounds_to(x, dv / df) or _rounds_to(x, dv * df):
                return True
    return False


def _range_derived(r: RangeMention, ctx: GuardContext, present: frozenset[float]) -> bool:
    for a, b in ctx.source_ranges:
        if a not in present or b not in present:
            continue
        da, db = Decimal(str(a)), Decimal(str(b))
        for f in ctx.factors:
            df = Decimal(str(f))
            if (_rounds_to(r.low, da / df) and _rounds_to(r.high, db / df)) or \
               (_rounds_to(r.low, da * df) and _rounds_to(r.high, db * df)):
                return True
    return False


class NumberGuard:
    """Áp bảng quyết định R0–R6 (design-data §4.3). Thuần, tất định."""

    def check(self, text: str, ctx: GuardContext) -> GuardVerdict:
        mentions, ranges = parse(text)
        range_by_low = {r.low.start: r for r in ranges}
        # Số quy đổi chỉ hợp lệ khi số gốc được nêu cùng đoạn ("250 mg/dL ≈ 13,9 mmol/L"); nếu không, mọi số
        # nguyên gần v/18 của bất kỳ số nào trong nguồn (vd 99/18 ≈ 6) đều lọt qua – xem Atlas, lệch §4.4.
        present = frozenset(m.value for m in mentions)
        bad: list[str] = []
        for m in mentions:
            raw = self._violation(m, range_by_low, ctx, present)
            if raw is not None and raw not in bad:
                bad.append(raw)
        return GuardVerdict(not bad, tuple(bad))

    @staticmethod
    def _violation(m: NumberMention, range_by_low: dict[int, RangeMention], ctx: GuardContext,
                   present: frozenset[float]) -> str | None:
        if m.role is NumberRole.RANGE_END:
            r = range_by_low.get(m.start)
            if r is None:                                                    # đầu cao: xét cùng đầu thấp
                return None
            if r.low.value in EXEMPT and r.high.value in EXEMPT:             # R0
                return None
            if (r.low.value, r.high.value) in ctx.source_ranges or _range_derived(r, ctx, present):  # R2, R5
                return None
            return r.raw
        if m.value in EXEMPT or m.value in ctx.source_values:                # R0, R1
            return None
        if m.role is NumberRole.PLAIN:
            if _derived(m, (ctx.source_values | ctx.user_values) & present, ctx.factors) or m.value in ctx.user_values:  # R3, R6
                return None
        elif _derived(m, ctx.source_values & present, ctx.factors):                    # R4
            return None
        return m.raw
