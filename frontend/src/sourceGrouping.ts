/** Chia nguồn của một câu trả lời thành 3 nhóm (design 2b, quy tắc nhóm C5). Hàm thuần. */
import type { Source } from './types.ts';
import { publisherFromTitle } from './format.ts';

export type SourceGroupKind = 'reviewed' | 'graph' | 'web';

export type SourceItem = {
  /** Chỉ số gốc 1-based trong mảng `sources` – thân câu trả lời trích theo số này. */
  n: number;
  source: Source;
  /** Tiêu đề hiển thị (nguồn đồ thị bỏ tiền tố). */
  title: string;
  /** Nhãn badge: cơ quan ban hành (nhóm đã duyệt) hoặc null (dùng badge mặc định của nhóm). */
  publisher: string | null;
  /** Chỉ số 1-based của nguồn trước đó có cùng URL. */
  sameAs?: number;
};

export type SourceGroup = { kind: SourceGroupKind; items: SourceItem[] };

const GRAPH_PREFIX = /^Đồ thị tri thức Neo4j:?\s*/;

export function sourceKind(s: Source): SourceGroupKind {
  if (s.review_status === 'curated_graph' || GRAPH_PREFIX.test(s.title)) return 'graph';
  if (s.review_status === 'unreviewed_web') return 'web';
  return 'reviewed'; // null / 'curated' / giá trị khác (B-1)
}

/** Thứ tự nhóm cố định: đã duyệt → đồ thị → web. Nhóm rỗng bị bỏ. */
export function groupSources(sources: Source[] | undefined): SourceGroup[] {
  const firstByUrl = new Map<string, number>();
  const buckets: Record<SourceGroupKind, SourceItem[]> = { reviewed: [], graph: [], web: [] };
  (sources ?? []).forEach((s, i) => {
    const kind = sourceKind(s);
    const first = s.url ? firstByUrl.get(s.url) : undefined;
    if (s.url && first === undefined) firstByUrl.set(s.url, i + 1);
    buckets[kind].push({
      n: i + 1,
      source: s,
      title: kind === 'graph' ? s.title.replace(GRAPH_PREFIX, '') : s.title,
      publisher: kind === 'reviewed' ? (s.publisher || publisherFromTitle(s.title, s.url)) : null,
      sameAs: first
    });
  });
  return (['reviewed', 'graph', 'web'] as const).filter(k => buckets[k].length).map(k => ({ kind: k, items: buckets[k] }));
}
