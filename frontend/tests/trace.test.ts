// Unit test REQ-DA-04 W-1: answerOutcome + gộp/dịch trace (design-ui.md mục 2c, ca T1–T11).
// Chạy: npm test (node --test, Node ≥ 22.18 tự bỏ type TypeScript; không cần thư viện test).
import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  answerOutcome, groupTrace, isBlockedTrace, needsEmergencyCall, formatTrace, stripRemovedNote, REMOVED_NOTE_V2, splitNums
} from '../src/trace.ts';
import { t, joinNums } from '../src/copy.ts';

const T1 = [
  'Coordinator', 'Rule Agent', 'Rule Agent (Approved)', 'Knowledge Agent (Retrieved 3 sources)',
  'Knowledge Graph Agent (3 facts, +1 linked docs)', 'Response Agent (Cited Generation)', 'Response Agent (Number check: passed)'
];
const PREFIX = ['Coordinator', 'Rule Agent', 'Rule Agent (Approved)', 'Knowledge Agent (Retrieved 3 sources)', 'Knowledge Graph Agent (3 facts, +1 linked docs)'];
const blockedRule = (cat: string) => ['Coordinator', 'Rule Agent', `Rule Agent (Blocked: ${cat})`, 'Response Agent (Safety Directive)'];

test('T1 trace mẫu thật → verified, đếm 3 tài liệu / 3 sự kiện / 1 tài liệu gốc, 4 bước', () => {
  const o = answerOutcome(T1);
  assert.equal(o.kind, 'verified');
  assert.equal(o.regenerated, false);
  assert.deepEqual([o.docs, o.facts, o.linkedDocs], [3, 3, 1]);
  const g = groupTrace(T1);
  assert.deepEqual(g.map(s => s.label), ['Kiểm tra an toàn', 'Tìm tài liệu', 'Tra đồ thị tri thức', 'Viết câu trả lời']);
  assert.deepEqual(g.map(s => s.status), ['ok', 'ok', 'ok', 'ok']);
  assert.deepEqual(g[0].details, ['Đạt: không có dấu hiệu cần dừng']); // dòng "Rule Agent" trống bị nuốt
  assert.deepEqual(g[1].details, ['Tìm thấy 3 tài liệu gần nghĩa']);
  assert.deepEqual(g[2].details, ['3 sự kiện từ đồ thị, kèm 1 tài liệu gốc']);
  assert.equal(g[3].details.length, 2);
  assert.equal(isBlockedTrace(T1), false);
});

test('T2 Rule Agent chặn EMERGENCY → rule-blocked, có Gọi 115', () => {
  const o = answerOutcome(blockedRule('EMERGENCY'));
  assert.equal(o.kind, 'rule-blocked');
  assert.equal(o.category, 'EMERGENCY');
  assert.equal(needsEmergencyCall(o), true);
  assert.equal(isBlockedTrace(blockedRule('EMERGENCY')), true);
  const rule = groupTrace(blockedRule('EMERGENCY'))[0];
  assert.equal(rule.status, 'blocked');
  assert.deepEqual(rule.details, ['Dừng: có dấu hiệu cấp cứu']);
});

test('T3 chặn PROMPT_INJECTION (và các loại khác) → rule-blocked, KHÔNG Gọi 115 (BUG-2)', () => {
  for (const cat of ['PROMPT_INJECTION', 'MEDICATION_DOSAGE', 'PII_SENSITIVE']) {
    const o = answerOutcome(blockedRule(cat));
    assert.equal(o.kind, 'rule-blocked');
    assert.equal(o.category, cat);
    assert.equal(needsEmergencyCall(o), false, cat);
  }
});

test('T4 Number check: blocked → number-blocked, KHÔNG phải chặn an toàn (BUG-1)', () => {
  const tr = [...PREFIX, 'Response Agent (Cited Generation)', 'Response Agent (Number check: blocked, unsupported: 77, 88)'];
  const o = answerOutcome(tr);
  assert.equal(o.kind, 'number-blocked');
  assert.deepEqual(o.unsupported, ['77', '88']);
  assert.equal(isBlockedTrace(tr), false);
  assert.equal(needsEmergencyCall(o), false);
  const resp = groupTrace(tr).at(-1)!;
  assert.equal(resp.status, 'blocked');
  assert.equal(resp.details[1], 'Đối chiếu số liệu: không hiển thị câu trả lời vì 77, 88 không có trong nguồn');
});

test('T5 filtered 1/3 (stream v2) → number-filtered, bước Viết "!"', () => {
  const tr = [...PREFIX, 'Response Agent (Cited Generation)', 'Response Agent (Number check: filtered 1/3 sentences, unsupported: 70–99)'];
  const o = answerOutcome(tr);
  assert.equal(o.kind, 'number-filtered');
  assert.deepEqual([o.removed, o.total], [1, 3]);
  assert.deepEqual(o.unsupported, ['70–99']);
  assert.equal(isBlockedTrace(tr), false);
  const resp = groupTrace(tr).at(-1)!;
  assert.equal(resp.status, 'warn');
  assert.equal(resp.details[1], 'Đối chiếu số liệu: lược 1/3 câu có số không có trong nguồn (70–99)');
});

test('T6 không có nguồn → no-source, docs 0', () => {
  const tr = ['Coordinator', 'Rule Agent', 'Rule Agent (Approved)', 'Knowledge Agent (Retrieved 0 sources)',
    'Knowledge Graph Agent (Skipped: no relevant source)', 'Response Agent (No source)'];
  const o = answerOutcome(tr);
  assert.equal(o.kind, 'no-source');
  assert.equal(o.docs, 0);
  const g = groupTrace(tr);
  assert.equal(g[1].status, 'skip');
  assert.deepEqual(g[1].details, ['Không có tài liệu đủ gần nghĩa']);
  assert.equal(g[2].status, 'skip');
});

test('T7 chỉ có nguồn web chưa duyệt → links-only', () => {
  const o = answerOutcome([...PREFIX, 'Response Agent (Links to unreviewed sources)']);
  assert.equal(o.kind, 'links-only');
});

test('T8 Conversation Agent → conversation, 2 bước', () => {
  const tr = ['Coordinator', 'Rule Agent', 'Rule Agent (Approved)', 'Conversation Agent'];
  assert.equal(answerOutcome(tr).kind, 'conversation');
  const g = groupTrace(tr);
  assert.deepEqual(g.map(s => s.label), ['Kiểm tra an toàn', 'Trò chuyện']);
});

test('T9 regenerated → verified + regenerated, bước Viết "!"', () => {
  const tr = [...PREFIX, 'Response Agent (Cited Generation)', 'Response Agent (Number check: regenerated, unsupported: 77)'];
  const o = answerOutcome(tr);
  assert.equal(o.kind, 'verified');
  assert.equal(o.regenerated, true);
  assert.equal(groupTrace(tr).at(-1)!.status, 'warn');
});

test('T10 agent lạ → unchecked, 1 bước nguyên văn', () => {
  const tr = ['Coordinator', 'Foo (Bar baz)'];
  assert.equal(answerOutcome(tr).kind, 'unchecked');
  const g = groupTrace(tr);
  assert.equal(g.length, 1);
  assert.equal(g[0].label, 'Foo');
  assert.deepEqual(g[0].details, ['Bar baz']);
  assert.equal(g[0].status, 'none');
});

test('T11 filtered không có unsupported → number-filtered, unsupported [], copy không ngoặc số', () => {
  for (const line of ['Response Agent (Number check: filtered 2/2 sentences)', 'Response Agent (Number check: filtered 2/2 sentences, unsupported: )']) {
    const tr = [...PREFIX, 'Response Agent (Cited Generation)', line];
    const o = answerOutcome(tr);
    assert.equal(o.kind, 'number-filtered', line);
    assert.deepEqual(o.unsupported, [], line);
    assert.equal(groupTrace(tr).at(-1)!.details[1], 'Đối chiếu số liệu: lược 2/2 câu có số không có trong nguồn', line);
  }
  assert.equal(t('outcome.filtered.noNums', { k: 2, n: 2 }), 'Đã lược 2/2 câu có số liệu nguồn không xác nhận. Phần còn lại khớp với nguồn.');
});

// --- Edge case bổ sung ---

test('thứ tự quyết định: rule-blocked thắng mọi dòng khác; number-blocked thắng no-source', () => {
  assert.equal(answerOutcome([...blockedRule('EMERGENCY'), 'Response Agent (Number check: blocked, unsupported: 1)']).kind, 'rule-blocked');
  assert.equal(answerOutcome(['Response Agent (No source)', 'Response Agent (Number check: blocked, unsupported: 5)']).kind, 'number-blocked');
});

test('trace rỗng / undefined → unchecked, không lỗi', () => {
  assert.equal(answerOutcome(undefined).kind, 'unchecked');
  assert.equal(answerOutcome([]).kind, 'unchecked');
  assert.deepEqual(groupTrace(undefined), []);
  assert.equal(isBlockedTrace(undefined), false);
});

test('v2 status skipped (không có dòng Number check) → unchecked', () => {
  assert.equal(answerOutcome([...PREFIX, 'Response Agent (Cited Generation)']).kind, 'unchecked');
});

test('category lạ vẫn rule-blocked, dịch "Dừng vì lý do an toàn", không Gọi 115', () => {
  const tr = blockedRule('SELF_HARM');
  const o = answerOutcome(tr);
  assert.equal(o.kind, 'rule-blocked');
  assert.equal(needsEmergencyCall(o), false);
  assert.deepEqual(groupTrace(tr)[0].details, ['Dừng vì lý do an toàn']);
});

test('chỉ gộp các dòng LIÊN TIẾP cùng agent', () => {
  const g = groupTrace(['Response Agent (Cited Generation)', 'Knowledge Agent (Retrieved 1 source)', 'Response Agent (Number check: passed)']);
  assert.equal(g.length, 3);
});

test('số thập phân kiểu Việt "6,5" không bị tách; danh sách > 3 số rút gọn bằng "…"', () => {
  assert.deepEqual(splitNums('6,5, 7,0'), ['6,5', '7,0']);
  assert.equal(joinNums(['1', '2', '3', '4']), '1, 2, 3, …');
});

test('SCR-4 formatTrace giữ Coordinator và bản dịch RL cũ', () => {
  const s = formatTrace(['Coordinator', 'Learning Agent (DQN Policy)']);
  assert.deepEqual(s.map(x => x.name), ['Coordinator', 'Learning Agent']);
  assert.equal(s[1].detail, 'Chính sách DQN chọn chủ đề');
});

test('REMOVED_NOTE: bỏ khi filtered và khớp nguyên văn; giữ tail web phía sau', () => {
  const filtered = answerOutcome(['Response Agent (Number check: filtered 1/3 sentences, unsupported: 70–99)']);
  const tail = '\n\nCác nguồn web tự động khác được hiển thị bên dưới.';
  assert.equal(stripRemovedNote('Câu A. Câu B.\n\n' + REMOVED_NOTE_V2 + tail, filtered), 'Câu A. Câu B.' + tail);
  assert.equal(stripRemovedNote('Câu A.\n\n' + REMOVED_NOTE_V2, filtered), 'Câu A.');
  // Không khớp nguyên văn → giữ nguyên.
  assert.equal(stripRemovedNote('Câu A.\n\nMột phần nội dung đã lược.', filtered), 'Câu A.\n\nMột phần nội dung đã lược.');
  // Không phải filtered → giữ nguyên.
  const verified = answerOutcome(T1);
  assert.equal(stripRemovedNote('X\n\n' + REMOVED_NOTE_V2, verified), 'X\n\n' + REMOVED_NOTE_V2);
});
