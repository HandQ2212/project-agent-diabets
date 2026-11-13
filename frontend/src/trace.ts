export type TraceStep = { name: string; detail: string; blocked: boolean };

const translations: [RegExp, (m: RegExpMatchArray) => string][] = [
  [/^Approved$/i, () => 'Đã duyệt, không có dấu hiệu nguy hiểm'],
  [/^Retrieved (\d+) sources?$/i, m => `Tìm thấy ${m[1]} tài liệu`],
  [/^(\d+) facts?,\s*\+(\d+) linked docs?$/i, m => `${m[1]} sự kiện từ đồ thị` + (Number(m[2]) > 0 ? `, kèm ${m[2]} tài liệu gốc` : '')],
  [/^Cited Generation$/i, () => 'Viết câu trả lời có trích dẫn nguồn'],
  [/^No source$/i, () => 'Không có nguồn phù hợp: trả lời từ chối, không suy diễn'],
  [/^Links to unreviewed sources$/i, () => 'Kèm nguồn web tự động, chưa được duyệt'],
  [/^Skipped:\s*no relevant source$/i, () => 'Bỏ qua: không có nguồn liên quan'],
  [/^Safety Directive$/i, () => 'Gửi hướng dẫn an toàn'],
  [/^Blocked:\s*EMERGENCY$/i, () => 'Dừng: phát hiện dấu hiệu cấp cứu'],
  [/^Blocked\b/i, () => 'Dừng: yêu cầu bị chặn vì lý do an toàn'],
  [/^DQN Policy$/i, () => 'Chính sách DQN chọn chủ đề'],
  [/^All modules completed$/i, () => 'Đã học hết các chủ đề']
];

function translateDetail(detail: string): string {
  for (const [re, fn] of translations) {
    const m = detail.match(re);
    if (m) return fn(m);
  }
  return detail; // không khớp bảng: giữ nguyên văn
}

/** Chuyển trace thô của backend thành các bước hiển thị: bỏ bước trùng, dịch phần chi tiết. */
export function formatTrace(trace: string[]): TraceStep[] {
  const parsed = trace.map(step => {
    const m = step.match(/^(.*?)\s*\((.*)\)\s*$/);
    return { name: m ? m[1] : step, detail: m ? m[2] : '' };
  });
  return parsed
    .filter((p, i) => !(p.detail === '' && parsed[i + 1]?.name === p.name && parsed[i + 1].detail !== ''))
    .map(p => ({ name: p.name, detail: p.detail ? translateDetail(p.detail) : '', blocked: /^Blocked\b/i.test(p.detail) }));
}

export const isBlockedTrace = (trace?: string[]) => !!trace?.some(s => /Blocked/i.test(s));
