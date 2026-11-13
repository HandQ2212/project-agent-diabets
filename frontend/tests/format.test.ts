// Unit test REQ-DA-04 W-3/W-5/W-6: hàm thuần định dạng, nhóm nguồn, /api/about, ngưỡng chờ.
// Ngày giờ phải ra giống nhau dù TZ máy là gì (npm test chạy được với TZ bất kỳ).
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { fmtDec, fmtPct, fmtInt, fmtDateVN, fmtDateTimeVN, publisherFromTitle, splitCitations } from '../src/format.ts';
import { groupSources, sourceKind } from '../src/sourceGrouping.ts';
import { classifyAbout, filterSources, kbDown, missingMetrics, FILTER_OTHER } from '../src/about.ts';
import { t } from '../src/copy.ts';

test('số kiểu Việt: 3 chữ số thập phân, phần trăm 1 chữ số, chấm nghìn, thiếu → "—"', () => {
  assert.equal(fmtDec(0.931), '0,931');
  assert.equal(fmtDec(1), '1,000');
  assert.equal(fmtPct(0.164), '16,4 %');
  assert.equal(fmtInt(418492), '418.492');
  assert.equal(fmtDec(null), '—');
  assert.equal(fmtPct(undefined), '—');
  assert.equal(fmtDec(Number.NaN), '—');
});

test(`ngày giờ theo Asia/Ho_Chi_Minh, độc lập TZ máy (TZ hiện tại: ${process.env.TZ ?? 'mặc định'})`, () => {
  assert.equal(fmtDateTimeVN('2026-11-13T14:05:00+07:00'), '13/11/2026 14:05');
  // 17:30 UTC = 00:30 hôm sau giờ VN (biên qua ngày).
  assert.equal(fmtDateTimeVN('2026-11-13T17:30:00Z'), '14/11/2026 00:30');
  assert.equal(fmtDateVN('2026-11-13T17:30:00Z'), '14/11/2026');
  assert.equal(fmtDateVN('2026-11-13T16:59:59Z'), '13/11/2026');
  // Chỉ có ngày → ngày lịch VN, không lệch.
  assert.equal(fmtDateVN('2026-11-12'), '12/11/2026');
  assert.equal(fmtDateVN('không phải ngày'), 'không phải ngày');
  assert.equal(fmtDateVN(null), '');
});

test('publisherFromTitle theo bảng design 2b', () => {
  assert.equal(publisherFromTitle('Bộ Y tế Việt Nam: Hướng dẫn …'), 'Bộ Y tế');
  assert.equal(publisherFromTitle('Tiêu chuẩn chẩn đoán (ADA 2026)'), 'ADA');
  assert.equal(publisherFromTitle('WHO: Diabetes'), 'WHO');
  assert.equal(publisherFromTitle('Báo cáo CDC'), 'CDC');
  assert.equal(publisherFromTitle('HbA1c là gì?', 'https://www.niddk.nih.gov/health'), 'NIDDK');
  assert.equal(publisherFromTitle('READAPT không phải ADA'), 'ADA'); // có từ ADA đứng riêng
  assert.equal(publisherFromTitle('READAPTATION'), null);
  assert.equal(publisherFromTitle('Bài viết', 'không phải url'), null);
});

test('splitCitations: [n] trong khoảng thành trích dẫn, ngoài khoảng/0 nguồn giữ text', () => {
  const p = splitCitations('A [2] B [9] C [0]', 3);
  assert.deepEqual(p, [{ kind: 'text', text: 'A ' }, { kind: 'cite', n: 2, raw: '[2]' }, { kind: 'text', text: ' B [9] C [0]' }]);
  assert.deepEqual(splitCitations('A [1]', 0), [{ kind: 'text', text: 'A [1]' }]);
  assert.deepEqual(splitCitations('', 2), []);
});

test('groupSources: thứ tự nhóm cố định, giữ số [n] gốc, badge cơ quan, trùng URL', () => {
  const g = groupSources([
    { title: 'Trang web', url: 'https://w', review_status: 'unreviewed_web' },
    { title: 'Đồ thị tri thức Neo4j: HbA1c', url: 'https://g', review_status: 'curated_graph' },
    { title: 'Tiêu chuẩn (ADA 2026)', url: 'https://a', review_status: null },
    { title: 'Bài khác', url: 'https://a', review_status: 'curated', publisher: 'WHO' }
  ]);
  assert.deepEqual(g.map(x => x.kind), ['reviewed', 'graph', 'web']);
  assert.deepEqual(g[0].items.map(i => [i.n, i.publisher, i.sameAs]), [[3, 'ADA', undefined], [4, 'WHO', 3]]);
  assert.equal(g[1].items[0].title, 'HbA1c');
  assert.equal(g[2].items[0].n, 1);
  assert.deepEqual(groupSources([]), []);
  assert.deepEqual(groupSources(undefined), []);
  assert.equal(sourceKind({ title: 'Đồ thị tri thức Neo4j: X', url: '' }), 'graph'); // fallback cũ theo tiêu đề
});

test('classifyAbout: 404 → not-ready, lỗi/5xx/JSON sai → error, 200 object → ok', () => {
  assert.deepEqual(classifyAbout(404, null), { state: 'not-ready' });
  assert.deepEqual(classifyAbout(500, null), { state: 'error' });
  assert.deepEqual(classifyAbout(null, null), { state: 'error' });
  assert.deepEqual(classifyAbout(200, [1, 2]), { state: 'error' });
  assert.deepEqual(classifyAbout(200, 'x'), { state: 'error' });
  assert.equal(classifyAbout(200, { models: [] }).state, 'ok');
});

test('Neo4j down và mô hình thiếu chỉ số', () => {
  assert.equal(kbDown({ kb: null }), true);
  assert.equal(kbDown({ kb: { error: 'neo4j unavailable' } }), true);
  assert.equal(kbDown({ kb: { topics: 1 } }), false);
  assert.equal(missingMetrics({ kind: 'x', name: 'x', metrics_test: null }), true);
  assert.equal(missingMetrics({ kind: 'x', name: 'x', metrics_test: { roc_auc: 0.9 } }), false);
});

test('lọc nguồn đã duyệt theo cơ quan, "Khác" = ngoài danh sách chính', () => {
  const list = [{ title: 'a', url: '1', publisher: 'ADA' }, { title: 'b', url: '2', publisher: null }, { title: 'c', url: '3', publisher: 'Sở Y tế' }];
  const known = ['Bộ Y tế', 'ADA'];
  assert.equal(filterSources(list, null, known).length, 3);
  assert.deepEqual(filterSources(list, 'ADA', known).map(s => s.title), ['a']);
  assert.deepEqual(filterSources(list, FILTER_OTHER, known).map(s => s.title), ['b', 'c']);
  assert.equal(filterSources(list, 'WHO', known).length, 0);
});

test('copy: biến thiếu giữ {x}, số định dạng vi-VN', () => {
  assert.equal(t('status.done', { n: 5 }), 'Đã trả lời xong, 5 nguồn.');
  assert.equal(t('data.src.count', { n: 1200 }), 'Đang hiện 1.200 tài liệu.');
  assert.equal(t('status.cite'), 'Đã chuyển tới nguồn [{n}].');
});

import { pendingLevel, doneStatus } from '../src/chatState.ts';

test('C1 ngưỡng chờ: <10 s checking, 10 s slow, 45 s very-slow (biên bao gồm)', () => {
  assert.equal(pendingLevel(0), 'checking');
  assert.equal(pendingLevel(9_999), 'checking');
  assert.equal(pendingLevel(10_000), 'slow');
  assert.equal(pendingLevel(44_999), 'slow');
  assert.equal(pendingLevel(45_000), 'very-slow');
  assert.equal(pendingLevel(600_000), 'very-slow');
});

test('#chat-status khi xong: bị chặn vì số / có nguồn / không nguồn', () => {
  assert.equal(doneStatus({ trace: ['Response Agent (Number check: blocked, unsupported: 77)'], sources: [{ title: 'a', url: 'b' }] }), t('status.blockedNum'));
  assert.equal(doneStatus({ trace: [], sources: [{ title: 'a', url: 'b' }, { title: 'c', url: 'd' }] }), 'Đã trả lời xong, 2 nguồn.');
  assert.equal(doneStatus({ trace: [], sources: [] }), 'Đã trả lời xong.');
});
