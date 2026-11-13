import type { Answer } from './types';

/** Phản hồi HTTP không thành công; `detail` là trường lỗi của API (nếu có). */
export class HttpError extends Error {
  constructor(public status: number, public detail?: unknown) {
    super(`HTTP ${status}`);
  }
}

/** Luồng trả lời kết thúc mà không có sự kiện `done`. */
export class StreamInterrupted extends Error {}

/** Máy chủ gửi sự kiện `error` trong luồng trả lời. */
export class StreamFailed extends Error {}

export const ERR_NETWORK = 'Không kết nối được tới máy chủ. Hãy kiểm tra kết nối rồi bấm Thử lại.';
export const ERR_SERVER = 'Hệ thống đang gặp sự cố. Vui lòng thử lại sau ít phút.';
export const ERR_INTERRUPTED = 'Kết nối bị gián đoạn. Phần đã nhận được giữ nguyên, bấm Thử lại để hỏi lại.';
export const ERR_GENERIC = 'Chưa xử lý được yêu cầu. Vui lòng thử lại.';

const VIETNAMESE = /[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]/i;

/** Chuyển mọi lỗi thành thông điệp tiếng Việt có hướng khắc phục; không bao giờ lộ `e.message` thô. */
export function friendlyError(e: unknown, status?: number): string {
  if (e instanceof StreamInterrupted) return ERR_INTERRUPTED;
  const code = e instanceof HttpError ? e.status : status;
  if (e instanceof TypeError) return ERR_NETWORK;
  if (e instanceof SyntaxError || e instanceof StreamFailed) return ERR_SERVER;
  if (code !== undefined && code >= 500) return ERR_SERVER;
  if (e instanceof HttpError && code !== undefined && code >= 400 && typeof e.detail === 'string' && VIETNAMESE.test(e.detail)) {
    return e.detail;
  }
  return ERR_GENERIC;
}

/**
 * Thông điệp lỗi cho luồng chat. `started`: đã nhận phản hồi HTTP OK; `received`: đã hiện một phần câu trả lời.
 * Sự kiện `error` sau khi đã có nội dung -> thông điệp gián đoạn (giữ phần đã nhận); chưa có nội dung -> lỗi máy chủ.
 */
export function chatErrorMessage(e: unknown, started: boolean, received: boolean): string {
  if (e instanceof StreamFailed) return received ? ERR_INTERRUPTED : ERR_SERVER;
  if (started && e instanceof TypeError) return ERR_INTERRUPTED;
  return friendlyError(e);
}

async function readDetail(r: Response): Promise<unknown> {
  try {
    return (await r.json()).detail;
  } catch {
    return undefined;
  }
}

export async function postApi(path: string, body: unknown): Promise<Answer> {
  const r = await fetch('/api/' + path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  if (!r.ok) throw new HttpError(r.status, await readDetail(r));
  return r.json(); // JSON hỏng -> SyntaxError -> friendlyError trả thông điệp máy chủ
}

export { readDetail };
