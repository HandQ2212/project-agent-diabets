"""Cơ quan ban hành (publisher) của tài liệu đã duyệt, tra tất định theo id Document (REQ-DA-04 B-2).

Nguồn sự thật là trường `publisher` của từng đoạn trong knowledge/sources*.json (gán tay theo license/URL).
Không lưu thêm vào Neo4j nên không cần seed lại hay nhúng lại embedding; truy xuất RAG đã trả `id` của Document.
Tài liệu web chưa duyệt và nguồn bộ ba đồ thị không có publisher (None).
"""
import json
import logging
from pathlib import Path
from typing import Iterable

log = logging.getLogger(__name__)

KNOWLEDGE_DIR = Path(__file__).resolve().parents[2] / 'knowledge'
SOURCE_FILES = ('sources.json', 'sources_v2.json')


def parse_publishers(entries: Iterable[dict]) -> dict[str, str]:
    """{id: publisher}. Lỗi ngay khi một đoạn thiếu publisher hoặc id trùng mà publisher khác nhau."""
    out: dict[str, str] = {}
    for entry in entries:
        doc_id, publisher = entry.get('id'), (entry.get('publisher') or '').strip()
        if not doc_id or not publisher:
            raise ValueError(f'Source entry {doc_id!r} has no publisher')
        if out.get(doc_id, publisher) != publisher:
            raise ValueError(f'Source {doc_id!r} has conflicting publishers')
        out[doc_id] = publisher
    return out


def load_publishers(directory: Path = KNOWLEDGE_DIR, files: Iterable[str] = SOURCE_FILES) -> dict[str, str]:
    entries = []
    for name in files:
        entries.extend(json.loads((directory / name).read_text(encoding='utf-8')))
    return parse_publishers(entries)


class PublisherRegistry:
    """Nạp trễ một lần. File thiếu/hỏng thì ghi cảnh báo và trả None (frontend tự đoán theo tiêu đề);
    dữ liệu đi kèm repo được test kiểm riêng để lỗi lộ ra ở CI chứ không ở lúc chạy."""

    def __init__(self, loader=load_publishers):
        self._loader = loader
        self._map: dict[str, str] | None = None

    def get(self, doc_id: str | None) -> str | None:
        if self._map is None:
            try:
                self._map = self._loader()
            except Exception:
                log.warning('Could not load source publishers; publisher will be null', exc_info=True)
                self._map = {}
        return self._map.get(doc_id) if doc_id else None


PUBLISHERS = PublisherRegistry()
