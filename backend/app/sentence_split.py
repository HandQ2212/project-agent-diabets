"""Tách luồng token của LLM thành câu hoàn chỉnh để hậu kiểm số từng câu trước khi phát (REQ-DA-03 §3.2).

Bất biến: ''.join(mọi câu trả ra) == ''.join(mọi token đã feed). Khoảng trắng sau dấu kết câu thuộc về câu
trước; một câu chỉ được trả khi đã thấy ký tự không phải khoảng trắng phía sau (hoặc khi flush), nên "5." +
"6" không bị tách thành hai câu.
"""
import re

MAX_SENTENCE_CHARS = 400

_END = re.compile(r'[.!?…]+["”’)\]]*\s+|\n\s*')
_LIST_PREFIX = re.compile(r'\s*(?:[-*•]\s*)?\d{1,2}')


class SentenceSplitter:
    """Nhận token theo luồng, trả các câu đã hoàn chỉnh."""

    def __init__(self) -> None:
        self._buf = ''

    def feed(self, token: str) -> list[str]:
        self._buf += token
        out: list[str] = []
        while True:
            cut = self._find_end(self._buf)
            if cut is None:
                break
            out.append(self._buf[:cut])
            self._buf = self._buf[cut:]
        while len(self._buf) > MAX_SENTENCE_CHARS:
            cut = self._buf.rfind(' ', 0, MAX_SENTENCE_CHARS) + 1 or MAX_SENTENCE_CHARS
            out.append(self._buf[:cut])
            self._buf = self._buf[cut:]
        return out

    def flush(self) -> list[str]:
        rest, self._buf = self._buf, ''
        return [rest] if rest else []

    @staticmethod
    def _find_end(buf: str) -> int | None:
        for m in _END.finditer(buf):
            if m.end() >= len(buf):        # chưa thấy ký tự sau khoảng trắng: có thể còn khoảng trắng / chưa chắc
                return None
            if buf[m.start()] != '\n':
                line_start = buf.rfind('\n', 0, m.start()) + 1
                if _LIST_PREFIX.fullmatch(buf[line_start:m.start()]):   # "1. " đầu dòng không phải hết câu
                    continue
            if not buf[:m.start()].strip():  # chỉ khoảng trắng: gộp vào câu sau
                continue
            return m.end()
        return None
