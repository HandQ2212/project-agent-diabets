/**
 * Đọc luồng NDJSON của `/api/chat/stream`. Cùng một code cho v1 (cả câu trả lời ~1 s trước `done`) và
 * v2 theo câu (REQ-DA-03), không cờ phiên bản. Sự kiện có `type` lạ (vd `stage`) hoặc sai kiểu → bỏ qua.
 */
import type { Source } from './types.ts';

export type StreamEvent =
  | { type: 'delta'; text: string }
  | { type: 'done'; sources: Source[]; trace: string[] }
  | { type: 'error' };

/** Chuẩn hoá một object JSON thành sự kiện UI hiểu; null = bỏ qua. */
export function toStreamEvent(raw: unknown): StreamEvent | null {
  if (!raw || typeof raw !== 'object') return null;
  const e = raw as Record<string, unknown>;
  if (e.type === 'delta') return typeof e.text === 'string' ? { type: 'delta', text: e.text } : null;
  if (e.type === 'done') {
    const sources = Array.isArray(e.sources) ? (e.sources as Source[]).filter(s => s && typeof s === 'object') : [];
    const trace = Array.isArray(e.trace) ? (e.trace as unknown[]).filter((x): x is string => typeof x === 'string') : [];
    return { type: 'done', sources, trace };
  }
  if (e.type === 'error') return { type: 'error' };
  return null;
}

/** Bộ đệm dòng: nhận từng mẩu text, trả các sự kiện đã đủ dòng. JSON hỏng ném SyntaxError (→ ERR_SERVER). */
export class NdjsonEventReader {
  private buffer = '';

  push(chunk: string): StreamEvent[] {
    this.buffer += chunk;
    const lines = this.buffer.split('\n');
    this.buffer = lines.pop() ?? '';
    return this.parse(lines);
  }

  /** Gọi khi luồng đóng: xử lý dòng cuối không có `\n`. */
  flush(): StreamEvent[] {
    const rest = this.buffer;
    this.buffer = '';
    return this.parse([rest]);
  }

  private parse(lines: string[]): StreamEvent[] {
    const out: StreamEvent[] = [];
    for (const line of lines) {
      if (!line.trim()) continue;
      const ev = toStreamEvent(JSON.parse(line));
      if (ev) out.push(ev);
    }
    return out;
  }
}
