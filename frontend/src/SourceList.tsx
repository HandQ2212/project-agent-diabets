import React from 'react';
import type { Source } from './types';
import { safeHref } from './format.ts';

function sourceKind(s: Source): { cls: string; label: string; note: string } {
  if (s.review_status === 'curated_graph' || s.title.startsWith('Đồ thị tri thức Neo4j')) {
    return { cls: 'graph', label: 'Đồ thị tri thức Neo4j', note: 'Sự kiện truy xuất từ đồ thị tri thức' };
  }
  if (s.review_status === 'unreviewed_web') {
    return { cls: 'web', label: 'Nguồn web chưa kiểm duyệt', note: 'Tự động thu thập, chỉ để tham khảo liên kết, chưa được kiểm duyệt chuyên môn' };
  }
  return { cls: 'curated', label: 'Tri thức đã tóm tắt', note: 'Bản tóm tắt được biên soạn thủ công từ nguồn chính thống' };
}

export function SourceList({ sources, compact }: { sources: Source[]; compact?: boolean }) {
  const firstIndexByUrl = new Map<string, number>();
  return (
    <div className={compact ? 'chat-sources' : 'sources-container'}>
      {compact ? <strong>Nguồn tham khảo</strong> : <h3>Nguồn tham khảo</h3>}
      <ul className="source-list">
        {sources.map((s, i) => {
          const k = sourceKind(s);
          const title = k.cls === 'graph' ? s.title.replace(/^Đồ thị tri thức Neo4j:\s*/, '') : s.title;
          const first = firstIndexByUrl.get(s.url);
          if (first === undefined) firstIndexByUrl.set(s.url, i);
          return (
            <li key={i} className={`src src-${k.cls}`}>
              <span className={`src-badge src-badge-${k.cls}`}>{k.label}</span>
              {safeHref(s.url)
                ? <a href={safeHref(s.url)!} target="_blank" rel="noreferrer">[{i + 1}] {title}<span className="sr-only"> (mở trong tab mới)</span> ↗</a>
                : <span>[{i + 1}] {title}</span>}
              <small>
                {k.note}{k.cls === 'web' && s.fetched_at ? ` · ${new Date(s.fetched_at).toLocaleDateString('vi-VN')}` : ''}
                {first !== undefined ? ` · Cùng liên kết với nguồn [${first + 1}]` : ''}
              </small>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
