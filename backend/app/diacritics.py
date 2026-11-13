"""Xử lý câu hỏi tiếng Việt gõ không dấu.

Embedding bge-m3 cho câu không dấu điểm thấp hơn hẳn câu có dấu (ví dụ 0.41 so với 0.73 với cùng
tài liệu), nên câu không dấu bị ngưỡng RAG loại. Module này khôi phục dấu bằng từ điển n-gram
(1..3 âm tiết) rút từ chính kho tri thức: mỗi cụm không dấu ánh xạ tới dạng có dấu xuất hiện nhiều
nhất, ghép tham lam theo cụm dài nhất. Cách này tất định và không cần LLM (thử với qwen3:4b thì
"tieu duong" bị khôi phục sai thành "tiêu dùng").

Từ điển KB chỉ phủ từ có trong tài liệu y khoa, nên từ hỏi đáp thường gặp ("co nen an chuoi",
"toi bi mat ngu") bị khôi phục theo nghĩa của KB ("cơ", "mắt"). Vì vậy có thêm TỪ VỰNG NỀN soạn tay,
tĩnh trong repo (vi_common_vocab.txt). Quy tắc chọn (chi tiết ở DiacriticRestorer):
  1. cụm dài hơn thắng, bất kể nguồn (nền hay KB);
  2. cùng độ dài: từ vựng nền thắng KB (nền soạn cho câu hỏi đời thường, KB chỉ có văn phong tài liệu);
  3. n-gram KB không được cắt ngang, hay đọc khác, một cụm >= 2 từ của từ vựng nền có trong câu;
  4. trong KB: dạng có dấu xuất hiện nhiều nhất, hoà thì theo thứ tự chữ cái.

Kết quả chỉ dùng để truy xuất (embedding); câu hỏi gốc vẫn được giữ cho Response Agent.
"""
from pathlib import Path
import logging
import re
import threading
import unicodedata
from collections import Counter, defaultdict
from typing import Iterable

log = logging.getLogger(__name__)

MAX_NGRAM = 3  # độ dài tối đa của n-gram rút từ KB; cụm của từ vựng nền có thể dài hơn
BASE_VOCAB_PATH = Path(__file__).with_name('vi_common_vocab.txt')
_WORD = re.compile(r'\w+')
# Chỉ ký tự chữ Latin có dấu (kể cả đ) mới tính là "có dấu"; chữ số, ký hiệu thì không.
_SEGMENT_BREAK = re.compile(r'[^\w\s]+')


def strip_diacritics(text: str) -> str:
    """Bỏ dấu tiếng Việt (đ -> d), giữ nguyên hoa/thường và ký tự khác."""
    text = text.replace('đ', 'd').replace('Đ', 'D')
    decomposed = unicodedata.normalize('NFD', text)
    return unicodedata.normalize('NFC', ''.join(c for c in decomposed if unicodedata.category(c) != 'Mn'))


def has_diacritics(text: str) -> bool:
    """True nếu văn bản có ít nhất một chữ mang dấu (bỏ dấu làm văn bản thay đổi)."""
    return strip_diacritics(unicodedata.normalize('NFC', text)) != unicodedata.normalize('NFC', text)


def parse_base_vocabulary(lines: Iterable[str]) -> dict[str, str]:
    """{cụm không dấu: cụm có dấu} từ các dòng của file từ vựng nền (bỏ dòng trống và '#').

    Hai mục khác nhau mà cùng dạng không dấu thì lỗi ngay (fail fast), vì sẽ không rõ chọn mục nào.
    """
    vocab: dict[str, str] = {}
    for number, raw in enumerate(lines, 1):
        phrase = ' '.join(unicodedata.normalize('NFC', raw.split('#', 1)[0]).lower().split())
        if not phrase:
            continue
        key = strip_diacritics(phrase)
        if key in vocab and vocab[key] != phrase:
            raise ValueError(f'base vocabulary line {number}: {phrase!r} collides with {vocab[key]!r}')
        vocab[key] = phrase
    return vocab


def load_base_vocabulary(path: Path = BASE_VOCAB_PATH) -> dict[str, str]:
    return parse_base_vocabulary(path.read_text(encoding='utf-8').splitlines())


class DiacriticRestorer:
    """Khôi phục dấu cho câu không dấu bằng từ điển {cụm không dấu: cụm có dấu}.

    Ghép tham lam từ trái sang phải; tại mỗi vị trí thử đoạn dài nhất trước (cụm dài hơn thắng):
      - cùng độ dài: từ vựng nền (`base`) thắng n-gram KB (`lexicon`);
      - n-gram KB bị loại nếu nó CẮT NGANG một cụm >= 2 từ của từ vựng nền có trong câu, hoặc chứa trọn
        cụm đó mà đọc khác ("de giam can" -> "để giảm cần" bị loại vì chứa "giảm cân"; "de giam" bị loại vì
        cắt ngang "giam can"). Từ đơn của từ vựng nền không khóa gì, để "an toàn", "nguy cơ" của KB
        vẫn thắng từ đơn "ăn";
      - không khớp gì thì giữ nguyên từ đó.
    """

    def __init__(self, lexicon: dict[str, str], base: dict[str, str] | None = None):
        self._lexicon = lexicon
        self._base = base or {}
        self._max_words = max([MAX_NGRAM, *(len(k.split()) for k in self._base)])

    def __len__(self) -> int:
        return len(self._lexicon) + len(self._base)

    @classmethod
    def from_texts(cls, texts: Iterable[str], base: dict[str, str] | None = None) -> 'DiacriticRestorer':
        counts: dict[str, Counter] = defaultdict(Counter)
        for text in texts:
            # Không ghép n-gram vượt qua dấu câu để tránh cụm vô nghĩa.
            for segment in _SEGMENT_BREAK.split(unicodedata.normalize('NFC', (text or '').lower())):
                words = segment.split()
                for n in range(1, MAX_NGRAM + 1):
                    for i in range(len(words) - n + 1):
                        gram = ' '.join(words[i:i + n])
                        counts[strip_diacritics(gram)][gram] += 1
        # Chọn dạng nhiều nhất; hoà thì lấy theo thứ tự chữ cái để kết quả tất định.
        lexicon = {key: min(forms.items(), key=lambda kv: (-kv[1], kv[0]))[0] for key, forms in counts.items()}
        return cls(lexicon, base)

    @staticmethod
    def _joinable(question: str, window) -> bool:
        """Các từ liền nhau chỉ cách bởi khoảng trắng (không ghép qua dấu câu)."""
        return not any(question[a.end():b.start()].strip() for a, b in zip(window, window[1:]))

    def _base_spans(self, question: str, tokens, words: list[str]) -> list[tuple[int, int, list[str]]]:
        """Mọi vị trí [a, b) trong câu khớp một cụm >= 2 từ của từ vựng nền, kèm các từ có dấu của cụm."""
        spans = []
        for a in range(len(tokens)):
            for b in range(a + 2, min(a + self._max_words, len(tokens)) + 1):
                phrase = self._base.get(' '.join(words[a:b]))
                if phrase is not None and self._joinable(question, tokens[a:b]):
                    spans.append((a, b, phrase.split()))
        return spans

    @staticmethod
    def _kb_allowed(i: int, j: int, restored: str, spans) -> bool:
        got = restored.split()
        for a, b, phrase in spans:
            if a < i or b <= i or j <= a:
                continue                      # không giao nhau, hoặc cụm nền bắt đầu trước i (đã bị bỏ qua)
            if not (i <= a and b <= j):
                return False                  # cắt ngang cụm nền
            if got[a - i:b - i] != phrase:
                return False                  # chứa cụm nền nhưng đọc khác
        return True

    def restore(self, question: str) -> str:
        """Trả câu đã khôi phục dấu; câu đã có dấu hoặc không có cụm nào trong từ điển thì giữ nguyên."""
        if not question or has_diacritics(question):
            return question
        tokens = list(_WORD.finditer(question))
        words = [t.group().lower() for t in tokens]
        spans = self._base_spans(question, tokens, words)
        pieces, cursor, i = [], 0, 0
        while i < len(tokens):
            n, restored = 1, None
            for size in range(min(self._max_words, len(tokens) - i), 0, -1):
                if not self._joinable(question, tokens[i:i + size]):
                    continue
                key = ' '.join(words[i:i + size])
                if key in self._base:
                    n, restored = size, self._base[key]
                    break
                kb = self._lexicon.get(key)
                if kb is not None and len(kb.split()) == size and self._kb_allowed(i, i + size, kb, spans):
                    n, restored = size, kb
                    break
            start, end = tokens[i].start(), tokens[i + n - 1].end()
            pieces.append(question[cursor:start])
            pieces.append(self._merge(window_tokens=tokens[i:i + n], original=question[start:end], restored=restored))
            cursor, i = end, i + n
        pieces.append(question[cursor:])
        return ''.join(pieces)

    @staticmethod
    def _merge(window_tokens, original: str, restored: str | None) -> str:
        """Từ nào được thêm dấu thì lấy dạng có dấu; từ nào không đổi thì giữ nguyên văn (hoa/thường như 'HbA1c')."""
        restored_words = (restored or '').split()
        if len(restored_words) != len(window_tokens):
            return original
        base = window_tokens[0].start()
        out, cursor = [], 0
        for token, word in zip(window_tokens, restored_words):
            start, end = token.start() - base, token.end() - base
            out.append(original[cursor:start])
            out.append(word if has_diacritics(word) else original[start:end])
            cursor = end
        return ''.join(out)


LEXICON_QUERY = '''
MATCH (d:Document) WHERE coalesce(d.review_status, '') <> 'unreviewed_web'
RETURN d.title AS title, d.text AS text
UNION ALL
MATCH (e:Entity) RETURN e.name AS title, reduce(s = '', a IN coalesce(e.aliases, []) | s + ' . ' + a) AS text
'''


class KnowledgeBaseRestorer:
    """Dựng DiacriticRestorer từ tài liệu đã kiểm duyệt + tên/alias thực thể trong Neo4j, cache theo tiến trình.

    Lỗi khi nạp không chặn truy xuất: trả câu gốc, không cache để lần sau thử lại.
    Kho được seed lại thì cần khởi động lại API (hoặc gọi reset()) để từ điển cập nhật.
    """

    def __init__(self, base: dict[str, str] | None = None):
        # File từ vựng nền nằm trong repo: hỏng/thiếu thì lỗi ngay lúc khởi động thay vì âm thầm bỏ qua.
        self._base = load_base_vocabulary() if base is None else base
        self._restorer: DiacriticRestorer | None = None
        self._lock = threading.Lock()

    def reset(self) -> None:
        with self._lock:
            self._restorer = None

    def _load(self, db) -> DiacriticRestorer | None:
        with self._lock:
            if self._restorer is None:
                records = db.execute_query(LEXICON_QUERY, database_='neo4j').records
                texts = [str(r.get(k) or '') for r in records for k in ('title', 'text')]
                restorer = DiacriticRestorer.from_texts(texts, self._base)
                if len(restorer) > len(self._base):
                    self._restorer = restorer
                else:
                    log.warning('Diacritic lexicon is empty; unaccented questions are searched as typed')
            return self._restorer

    def restore(self, question: str, db) -> str:
        if not question or has_diacritics(question):
            return question
        try:
            restorer = self._load(db)
        except Exception:
            log.warning('Could not build diacritic lexicon; searching the question as typed', exc_info=True)
            return question
        return restorer.restore(question) if restorer else question
