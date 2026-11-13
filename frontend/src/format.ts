/**
 * Định dạng số và ngày giờ cho REQ-DA-04. Hàm thuần, kết quả không phụ thuộc múi giờ máy:
 * ngày giờ luôn hiển thị theo Asia/Ho_Chi_Minh (luật chung DevFactory).
 */
const VN_TZ = 'Asia/Ho_Chi_Minh';

const isNum = (n: unknown): n is number => typeof n === 'number' && Number.isFinite(n);

/** 3 chữ số thập phân kiểu Việt: 0.931 → "0,931". Không có số → "—". */
export function fmtDec(n: number | null | undefined, digits = 3): string {
  return isNum(n) ? n.toLocaleString('vi-VN', { minimumFractionDigits: digits, maximumFractionDigits: digits }) : '—';
}

/** Tỉ lệ 0–1 → phần trăm 1 chữ số: 0.164 → "16,4 %". */
export function fmtPct(rate: number | null | undefined): string {
  return isNum(rate) ? (rate * 100).toLocaleString('vi-VN', { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + ' %' : '—';
}

/** Số lượng có dấu chấm nghìn: 418492 → "418.492". */
export function fmtInt(n: number | null | undefined): string {
  return isNum(n) ? Math.round(n).toLocaleString('vi-VN') : '—';
}

function vnParts(iso: string | null | undefined): Record<string, string> | null {
  if (!iso) return null;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return null;
  const parts = new Intl.DateTimeFormat('en-GB', {
    timeZone: VN_TZ, day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit', hourCycle: 'h23'
  }).formatToParts(d);
  return Object.fromEntries(parts.map(p => [p.type, p.value]));
}

/**
 * `dd/MM/yyyy` theo giờ VN. Chuỗi chỉ có ngày (`YYYY-MM-DD`) được hiểu là ngày lịch VN, không đổi múi giờ.
 * Không đọc được → trả lại nguyên văn (không mất thông tin), rỗng → "".
 */
export function fmtDateVN(iso: string | null | undefined): string {
  if (!iso) return '';
  const dateOnly = iso.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (dateOnly) return `${dateOnly[3]}/${dateOnly[2]}/${dateOnly[1]}`;
  const p = vnParts(iso);
  return p ? `${p.day}/${p.month}/${p.year}` : iso;
}

/** `dd/MM/yyyy HH:mm` theo giờ VN. */
export function fmtDateTimeVN(iso: string | null | undefined): string {
  const p = vnParts(iso);
  return p ? `${p.day}/${p.month}/${p.year} ${p.hour}:${p.minute}` : (iso ?? '');
}

export const PUBLISHERS = ['Bộ Y tế', 'ADA', 'WHO', 'CDC', 'NIDDK'] as const;

/**
 * Suy cơ quan ban hành từ tiêu đề (fallback tạm cho tới khi backend có `publisher` – design 2b, B-2).
 * Thứ tự ưu tiên theo bảng design. Không suy được → null.
 */
export function publisherFromTitle(title: string, url?: string): string | null {
  if (/Bộ Y tế/i.test(title)) return 'Bộ Y tế';
  if (/\bADA\b/.test(title)) return 'ADA';
  if (/^WHO\b|\bWHO:/.test(title)) return 'WHO';
  if (/\bCDC\b/.test(title)) return 'CDC';
  if (/NIDDK/.test(title)) return 'NIDDK';
  if (url) {
    try { if (/(^|\.)niddk\.nih\.gov$/i.test(new URL(url).hostname)) return 'NIDDK'; } catch { /* URL hỏng: bỏ qua */ }
  }
  return null;
}

export type CitePart = { kind: 'text'; text: string } | { kind: 'cite'; n: number; raw: string };

/**
 * Tách `[n]` trong câu trả lời. `[n]` chỉ thành trích dẫn khi 1 ≤ n ≤ sourceCount; ngoài khoảng hoặc
 * sourceCount = 0 (đang stream) → giữ text thường (design SCR-1.C2).
 */
export function splitCitations(text: string, sourceCount: number): CitePart[] {
  const out: CitePart[] = [];
  const re = /\[(\d{1,3})\]/g;
  let last = 0;
  let m: RegExpExecArray | null;
  const pushText = (s: string) => {
    if (!s) return;
    const prev = out[out.length - 1];
    if (prev?.kind === 'text') prev.text += s; else out.push({ kind: 'text', text: s });
  };
  while ((m = re.exec(text))) {
    const n = Number(m[1]);
    pushText(text.slice(last, m.index));
    if (n >= 1 && n <= sourceCount) out.push({ kind: 'cite', n, raw: m[0] });
    else pushText(m[0]);
    last = m.index + m[0].length;
  }
  pushText(text.slice(last));
  return out;
}
