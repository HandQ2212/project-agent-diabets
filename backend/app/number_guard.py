"""Hậu kiểm tất định: mọi con số trong câu trả lời phải xuất hiện trong ngữ cảnh nguồn.

Model nhỏ hay "nhớ" các ngưỡng y khoa từ dữ liệu huấn luyện (ví dụ 70–99 mg/dL) dù không có trong nguồn.
Mô-đun này không gọi LLM: trích số, chuẩn hóa (dấu phẩy/chấm thập phân, dấu phân cách hàng nghìn, khoảng
"70–99" thành hai số) rồi đối chiếu với số có trong nguồn và trong câu hỏi.
"""
import re

# Số đứng riêng: không dính chữ (HbA1c, PMC123, dc26-S005 bị loại), cho phép "1.000" (hàng nghìn) và "5,6" / "5.6".
_NUMBER = re.compile(r'(?<![\w])(\d{1,3}(?:\.\d{3})+(?!\d)|\d+(?:[.,]\d+)?)')
_CITATION = re.compile(r'\[\d+\]')
_LIST_MARK = re.compile(r'(?m)^\s*(?:[-*•]\s*)?\d{1,2}[.)]\s+')
# Số đếm rất nhỏ (1–2) xuất hiện tự nhiên trong lời văn; mọi số khác phải có trong nguồn.
EXEMPT = {0.0, 1.0, 2.0}


def normalize(raw: str) -> float:
    """'5,6' và '5.6' -> 5.6; '1.000' -> 1000.0."""
    if re.fullmatch(r'\d{1,3}(?:\.\d{3})+', raw):
        raw = raw.replace('.', '')
    return round(float(raw.replace(',', '.')), 6)


def extract_numbers(text: str) -> list[tuple[str, float]]:
    cleaned = _LIST_MARK.sub('', _CITATION.sub(' ', text))
    return [(m.group(1), normalize(m.group(1))) for m in _NUMBER.finditer(cleaned)]


def allowed_values(*texts: str) -> set[float]:
    values: set[float] = set()
    for text in texts:
        values.update(value for _, value in extract_numbers(text))
    return values


def find_unsupported(answer: str, *context: str) -> list[str]:
    """Trả về các số (nguyên văn, không trùng) trong answer mà không có trong context."""
    allowed = allowed_values(*context) | EXEMPT
    seen, bad = set(), []
    for raw, value in extract_numbers(answer):
        if value not in allowed and value not in seen:
            seen.add(value)
            bad.append(raw)
    return bad
