/**
 * `GET /api/about` – kiểu theo design-ui.md mục 6c. Endpoint do backend (Rex) làm; frontend chỉ gọi.
 * Khi endpoint chưa có (404) SCR-2 hiện `data.error.notReady` + trạng thái từ `/api/health`.
 */
export type ModelKind = 'symptoms' | 'brfss' | 'nhanes_research' | 'nhanes15_research';

export type ModelInfo = {
  kind: ModelKind | string;
  name: string;
  architecture?: string | null;
  available?: boolean;
  dataset?: {
    name?: string | null; cycles?: string[] | null; label?: string | null;
    n_train?: number | null; n_validation?: number | null; n_test?: number | null; positive_rate_test?: number | null;
  } | null;
  threshold?: number | null;
  metrics_test?: {
    roc_auc?: number | null; f1_pos?: number | null; recall_pos?: number | null; precision_pos?: number | null;
    accuracy?: number | null; brier?: number | null; confusion_matrix?: number[][] | null; auc_ci95?: [number, number] | null;
  } | null;
  baseline?: { name: string; split?: string | null; roc_auc?: number | null; f1_pos?: number | null } | null;
  selection_rule?: string | null;
  limitations?: string[] | null;
};

export type RlInfo = {
  episodes_per_seed?: number | null;
  seeds?: number | null;
  results: { policy: string; mean_return: number; std_return?: number | null }[];
};

export type AssistantInfo = {
  llm?: string | null; llm_provider?: string | null; embedding?: string | null; embedding_dim?: number | null;
  top_k?: number | null; min_cosine?: number | null; vector_index?: boolean | null; number_guard?: string | null;
};

export type ReviewedSource = { title: string; url: string; publisher?: string | null; topic?: string | null; date?: string | null };

export type KbInfo = {
  reviewed_chunks?: number | null; reviewed_docs?: number | null; web_chunks?: number | null; web_pages?: number | null;
  topics?: number | null; entities?: number | null; relations?: number | null;
  relations_by_type?: { type: string; count: number }[] | null;
  topic_names?: string[] | null;
  reviewed_sources?: ReviewedSource[] | null;
  error?: string | null;
};

export type AboutInfo = {
  generated_at?: string | null;
  models?: ModelInfo[] | null;
  rl?: RlInfo | null;
  assistant?: AssistantInfo | null;
  kb?: KbInfo | null;
  limitations?: string[] | null;
};

export type AboutResult =
  | { state: 'ok'; data: AboutInfo }
  | { state: 'not-ready' }   // 404: endpoint chưa có
  | { state: 'error' };      // mạng, 5xx, JSON hỏng

/** Kết quả fetch → trạng thái SCR-2. Tách khỏi `fetch` để test thuần. */
export function classifyAbout(status: number | null, body: unknown): AboutResult {
  if (status === 404) return { state: 'not-ready' };
  if (status === null || status < 200 || status >= 300) return { state: 'error' };
  if (!body || typeof body !== 'object' || Array.isArray(body)) return { state: 'error' };
  return { state: 'ok', data: body as AboutInfo };
}

export async function fetchAbout(signal?: AbortSignal): Promise<AboutResult> {
  let r: Response;
  try {
    r = await fetch('/api/about', { signal });
  } catch (e) {
    if (signal?.aborted) throw e;
    return classifyAbout(null, null);
  }
  if (!r.ok) return classifyAbout(r.status, null);
  try {
    return classifyAbout(r.status, await r.json());
  } catch {
    return classifyAbout(null, null);
  }
}

/** Neo4j lỗi: `kb` null hoặc có `error` (3a-2). */
export const kbDown = (a: AboutInfo) => !a.kb || !!a.kb.error;

/** Mô hình thiếu chỉ số (partial). */
export const missingMetrics = (m: ModelInfo) => !m.metrics_test || m.metrics_test.roc_auc == null;

export const FILTER_OTHER = '__other__';

/** Lọc nguồn đã duyệt theo cơ quan; `Khác` = không thuộc danh sách cơ quan chính. */
export function filterSources(list: ReviewedSource[], filter: string | null, known: readonly string[]): ReviewedSource[] {
  if (!filter) return list;
  if (filter === FILTER_OTHER) return list.filter(s => !s.publisher || !known.includes(s.publisher));
  return list.filter(s => s.publisher === filter);
}
