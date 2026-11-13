// Unit test REQ-DA-04: đọc NDJSON v1 và v2 bằng cùng một code; type lạ bị bỏ qua (design 3a-1).
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { NdjsonEventReader, toStreamEvent } from '../src/stream.ts';

const line = (o: unknown) => JSON.stringify(o) + '\n';
const DONE = { type: 'done', sources: [{ title: 'a', url: 'u' }], trace: ['Coordinator', 'Response Agent (Number check: passed)'] };

test('v1: một delta cả câu rồi done', () => {
  const r = new NdjsonEventReader();
  const ev = r.push(line({ type: 'delta', text: 'Toàn bộ câu trả lời.' }) + line(DONE));
  assert.deepEqual(ev.map(e => e.type), ['delta', 'done']);
});

test('v2: delta theo câu, dòng bị cắt giữa hai mẩu, sự kiện stage/type lạ bị bỏ qua', () => {
  const r = new NdjsonEventReader();
  const full = line({ type: 'stage', name: 'rule' }) + line({ type: 'delta', text: 'Câu 1. ' }) + line({ type: 'heartbeat' })
    + line({ type: 'delta', text: 'Câu 2.' }) + line({ ...DONE, trace: ['Response Agent (Number check: filtered 1/3 sentences, unsupported: 70–99)'] });
  const cut = Math.floor(full.length / 2);
  const ev = [...r.push(full.slice(0, cut)), ...r.push(full.slice(cut)), ...r.flush()];
  assert.deepEqual(ev.map(e => e.type), ['delta', 'delta', 'done']);
  assert.equal(ev.filter(e => e.type === 'delta').map(e => (e as { text: string }).text).join(''), 'Câu 1. Câu 2.');
});

test('dòng cuối không có \\n vẫn được xử lý khi flush; dòng trống bỏ qua', () => {
  const r = new NdjsonEventReader();
  assert.deepEqual(r.push('\n\n' + JSON.stringify(DONE)), []);
  assert.deepEqual(r.flush().map(e => e.type), ['done']);
});

test('sự kiện error → error; JSON hỏng → SyntaxError (UI hiện ERR_SERVER)', () => {
  assert.deepEqual(new NdjsonEventReader().push(line({ type: 'error', message: 'x' })), [{ type: 'error' }]);
  assert.throws(() => new NdjsonEventReader().push('{hỏng\n'), SyntaxError);
});

test('toStreamEvent bỏ sự kiện sai kiểu, lọc trace/sources không hợp lệ', () => {
  assert.equal(toStreamEvent({ type: 'delta', text: 5 }), null);
  assert.equal(toStreamEvent(null), null);
  assert.equal(toStreamEvent('chuỗi'), null);
  assert.deepEqual(toStreamEvent({ type: 'done', sources: 'x', trace: ['a', 1, null] }), { type: 'done', sources: [], trace: ['a'] });
});
