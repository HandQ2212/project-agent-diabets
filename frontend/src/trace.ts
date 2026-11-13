/**
 * Phân tích trace của hệ đa tác tử (REQ-DA-04 design-ui.md mục 2c). Hàm thuần, không phụ thuộc React.
 * Dùng chung cho NDJSON v1 và stream theo câu v2 (REQ-DA-03): chỉ đọc `done.trace`, không cần cờ phiên bản.
 */
import { t, joinNums, type CopyKey } from './copy.ts';

export type AnswerOutcomeKind =
  | 'rule-blocked' | 'conversation' | 'no-source' | 'links-only'
  | 'number-blocked' | 'number-filtered' | 'verified' | 'unchecked';

export type AnswerOutcome = {
  kind: AnswerOutcomeKind;
  category?: 'EMERGENCY' | 'MEDICATION_DOSAGE' | 'PII_SENSITIVE' | 'PROMPT_INJECTION' | string;
  regenerated?: boolean;
  removed?: number;
  total?: number;
  unsupported?: string[];
  docs?: number;
  facts?: number;
  linkedDocs?: number;
};

/** Trạng thái một bước: ok ✓, skip –, warn !, blocked ✕, none (không icon). */
export type StepStatus = 'ok' | 'skip' | 'warn' | 'blocked' | 'none';

export type TraceGroup = {
  /** Tên agent gốc từ backend (dùng chọn màu). */
  name: string;
  /** Nhãn tiếng Việt, hoặc nguyên văn nếu agent lạ. */
  label: string;
  /** Phụ đề nhỏ (tên agent kỹ thuật), có thể rỗng. */
  subtitle: string;
  status: StepStatus;
  details: string[];
};

/**
 * Bản sao NGUYÊN VĂN `REMOVED_NOTE` của backend.
 * Nguồn: backend/app/number_guard.py (nhánh req-da-03/t1-t3, dòng 27). Backend đổi chữ thì cập nhật ở đây;
 * không khớp thì UI giữ nguyên thân câu trả lời (design 3a-1).
 */
export const REMOVED_NOTE_V2 = 'Một phần nội dung có con số chưa được nguồn xác nhận nên đã được lược bỏ; vui lòng xem nguồn bên dưới.';

const LINE = /^(.*?)\s*\((.*)\)\s*$/;

export function parseLine(line: string): { name: string; detail: string } {
  const m = line.match(LINE);
  return { name: (m ? m[1] : line).trim(), detail: m ? m[2].trim() : '' };
}

const RULE_BLOCKED = /^Rule Agent \(Blocked:\s*(\w+)\)$/i;
const NUM_BLOCKED = /Number check: blocked(?:, unsupported: ?(.*?))?\)?$/i;
const NUM_FILTERED = /Number check: filtered (\d+)\/(\d+) sentences?(?:, unsupported: ?(.*?))?\)?$/i;
const NUM_REGENERATED = /Number check: regenerated(?:, unsupported: ?(.*?))?\)?$/i;
const NUM_PASSED = /Number check: passed/i;
const RETRIEVED = /^Knowledge Agent \(Retrieved (\d+) sources?\)$/i;
const FACTS = /^Knowledge Graph Agent \((\d+) facts?,\s*\+(\d+) linked docs?\)$/i;

/** Tách danh sách số backend nối bằng ", " (số thập phân kiểu "6,5" không có khoảng trắng nên không bị tách). */
export function splitNums(raw: string | undefined): string[] {
  if (!raw) return [];
  return raw.split(', ').map(s => s.trim()).filter(Boolean);
}

/** Phân loại kết quả của một lượt trả lời theo bảng quyết định 2c (gặp điều kiện đầu tiên thì dừng). */
export function answerOutcome(trace: string[] | undefined): AnswerOutcome {
  const lines = (trace ?? []).map(s => s.trim());
  const counts: Pick<AnswerOutcome, 'docs' | 'facts' | 'linkedDocs'> = {};
  for (const line of lines) {
    const r = line.match(RETRIEVED);
    if (r) counts.docs = Number(r[1]);
    const f = line.match(FACTS);
    if (f) { counts.facts = Number(f[1]); counts.linkedDocs = Number(f[2]); }
  }
  const find = (re: RegExp) => {
    for (const line of lines) { const m = line.match(re); if (m) return m; }
    return null;
  };

  const rule = find(RULE_BLOCKED);
  if (rule) return { kind: 'rule-blocked', category: rule[1].toUpperCase(), ...counts }; // category chuẩn hoá chữ hoa (TC-BUG2.6)
  if (lines.some(l => parseLine(l).name === 'Conversation Agent')) return { kind: 'conversation', ...counts };
  const blocked = find(NUM_BLOCKED);
  if (blocked) return { kind: 'number-blocked', unsupported: splitNums(blocked[1]), ...counts };
  const filtered = find(NUM_FILTERED);
  if (filtered) {
    return { kind: 'number-filtered', removed: Number(filtered[1]), total: Number(filtered[2]), unsupported: splitNums(filtered[3]), ...counts };
  }
  if (lines.includes('Response Agent (No source)')) return { kind: 'no-source', ...counts };
  if (lines.includes('Response Agent (Links to unreviewed sources)')) return { kind: 'links-only', ...counts };
  const regen = find(NUM_REGENERATED);
  if (regen) return { kind: 'verified', regenerated: true, unsupported: splitNums(regen[1]), ...counts };
  if (find(NUM_PASSED)) return { kind: 'verified', regenerated: false, ...counts };
  return { kind: 'unchecked', ...counts };
}

/** Sửa BUG-1: chỉ Rule Agent chặn mới là chặn an toàn; "Number check: blocked" KHÔNG phải. */
export const isBlockedTrace = (trace?: string[]) => answerOutcome(trace).kind === 'rule-blocked';

/** Chỉ EMERGENCY mới hiện Gọi 115 (BUG-2). */
export const needsEmergencyCall = (o: AnswerOutcome) => o.kind === 'rule-blocked' && o.category?.toUpperCase() === 'EMERGENCY';

type Translated = { text: string; status: StepStatus };

const BLOCKED_KEYS: Record<string, CopyKey> = {
  EMERGENCY: 'trace.d.blocked.emergency',
  MEDICATION_DOSAGE: 'trace.d.blocked.dosage',
  PII_SENSITIVE: 'trace.d.blocked.pii',
  PROMPT_INJECTION: 'trace.d.blocked.injection'
};

const DETAILS: [RegExp, (m: RegExpMatchArray) => Translated][] = [
  [/^Approved$/i, () => ({ text: t('trace.d.approved'), status: 'ok' })],
  [/^Blocked:\s*(\w+)$/i, m => ({ text: t(BLOCKED_KEYS[m[1].toUpperCase()] ?? 'trace.d.blocked.other'), status: 'blocked' })],
  [/^Blocked\b/i, () => ({ text: t('trace.d.blocked.other'), status: 'blocked' })],
  [/^Retrieved (\d+) sources?$/i, m => Number(m[1]) > 0
    ? { text: t('trace.d.retrieved', { n: Number(m[1]) }), status: 'ok' }
    : { text: t('trace.d.retrieved0'), status: 'skip' }],
  [/^(\d+) facts?,\s*\+(\d+) linked docs?$/i, m => ({
    text: t('trace.d.facts', { n: Number(m[1]) }) + (Number(m[2]) > 0 ? t('trace.d.factsLinked', { m: Number(m[2]) }) : ''),
    status: Number(m[1]) > 0 ? 'ok' : 'skip'
  })],
  [/^No matching entity$/i, () => ({ text: t('trace.d.noEntity'), status: 'skip' })],
  [/^Skipped:\s*no relevant source$/i, () => ({ text: t('trace.d.graphSkipped'), status: 'skip' })],
  [/^Cited Generation$/i, () => ({ text: t('trace.d.cited'), status: 'ok' })],
  [/^No source$/i, () => ({ text: t('trace.d.nosource'), status: 'ok' })],
  [/^Links to unreviewed sources$/i, () => ({ text: t('trace.d.linksOnly'), status: 'ok' })],
  [/^Safety Directive$/i, () => ({ text: t('trace.d.safety'), status: 'ok' })],
  [/^Number check: passed$/i, () => ({ text: t('trace.d.num.passed'), status: 'ok' })],
  [/^Number check: regenerated(?:, unsupported: ?(.*))?$/i, m => ({
    text: t('trace.d.num.regenerated', { nums: joinNums(splitNums(m[1])) }), status: 'warn'
  })],
  [/^Number check: filtered (\d+)\/(\d+) sentences?(?:, unsupported: ?(.*))?$/i, m => {
    const nums = splitNums(m[3]);
    const vars = { k: Number(m[1]), n: Number(m[2]), nums: joinNums(nums) };
    return { text: nums.length ? t('trace.d.num.filtered', vars) : t('trace.d.num.filteredNoNums', vars), status: 'warn' };
  }],
  [/^Number check: blocked(?:, unsupported: ?(.*))?$/i, m => ({
    text: t('trace.d.num.blocked', { nums: joinNums(splitNums(m[1])) }), status: 'blocked'
  })],
  // SCR-4 (Mô phỏng RL) – giữ bản dịch cũ.
  [/^DQN Policy$/i, () => ({ text: 'Chính sách DQN chọn chủ đề', status: 'none' })],
  [/^All modules completed$/i, () => ({ text: 'Đã học hết các chủ đề', status: 'none' })]
];

/** Dịch phần chi tiết; không khớp mẫu nào thì giữ nguyên văn (không mất thông tin). */
export function translateDetail(detail: string): Translated {
  for (const [re, fn] of DETAILS) {
    const m = detail.match(re);
    if (m) return fn(m);
  }
  return { text: detail, status: 'none' };
}

const AGENTS: Record<string, { key: CopyKey; subtitle: string }> = {
  'Rule Agent': { key: 'trace.step.rule', subtitle: 'Rule Agent' },
  'Knowledge Agent': { key: 'trace.step.knowledge', subtitle: 'Knowledge Agent · RAG' },
  'Knowledge Graph Agent': { key: 'trace.step.graph', subtitle: 'Knowledge Graph Agent · Neo4j' },
  'Response Agent': { key: 'trace.step.response', subtitle: 'Response Agent · LLM' },
  'Conversation Agent': { key: 'trace.step.conversation', subtitle: 'Conversation Agent' }
};

const SEVERITY: StepStatus[] = ['none', 'ok', 'skip', 'warn', 'blocked'];
const worst = (a: StepStatus, b: StepStatus) => (SEVERITY.indexOf(b) > SEVERITY.indexOf(a) ? b : a);

/**
 * Gộp các dòng liên tiếp cùng tên agent thành một bước có nhiều dòng chi tiết (C6).
 * Dòng không có chi tiết bị nuốt nếu bước đó có chi tiết khác. `keepCoordinator`: SCR-4 vẫn hiện Coordinator.
 */
export function groupTrace(trace: string[] | undefined, opts: { keepCoordinator?: boolean } = {}): TraceGroup[] {
  const groups: TraceGroup[] = [];
  for (const raw of trace ?? []) {
    const { name, detail } = parseLine(raw.trim());
    if (!name) continue;
    if (name === 'Coordinator' && !opts.keepCoordinator) continue;
    let g = groups[groups.length - 1];
    if (!g || g.name !== name) {
      const agent = AGENTS[name];
      g = { name, label: agent ? t(agent.key) : name, subtitle: agent?.subtitle ?? '', status: agent ? 'ok' : 'none', details: [] };
      groups.push(g);
    }
    if (!detail) continue;
    const tr = translateDetail(detail);
    g.details.push(tr.text);
    if (AGENTS[name]) {
      const s = tr.status === 'none' ? 'ok' : tr.status;
      g.status = g.details.length === 1 ? s : worst(g.status, s);
    }
  }
  return groups;
}

/** Tương thích SCR-4 (`TracePipeline`): mỗi bước 1 dòng chi tiết. */
export type TraceStep = { name: string; detail: string; blocked: boolean };
export function formatTrace(trace: string[]): TraceStep[] {
  return groupTrace(trace, { keepCoordinator: true }).map(g => ({
    name: g.name, detail: g.details.join(' · '), blocked: g.status === 'blocked'
  }));
}

/**
 * Bỏ đoạn REMOVED_NOTE khỏi thân khi outcome là number-filtered và khớp nguyên văn (design 3a-1).
 * Không khớp → trả nguyên văn (chấp nhận lặp ý, không mất thông tin).
 */
export function stripRemovedNote(text: string, outcome: AnswerOutcome): string {
  if (outcome.kind !== 'number-filtered' || !text.includes(REMOVED_NOTE_V2)) return text;
  const i = text.indexOf(REMOVED_NOTE_V2);
  return text.slice(0, i).replace(/\s+$/, '') + text.slice(i + REMOVED_NOTE_V2.length);
}
