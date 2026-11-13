/** Trạng thái lượt chat dùng chung (hàm thuần, test được) – design 3a-1, 3b, 4b. */
import { t } from './copy.ts';
import { answerOutcome } from './trace.ts';
import type { ChatTurn } from './types.ts';

export const SLOW_MS = 10_000;
export const VERY_SLOW_MS = 45_000;
export const SHOW_ELAPSED_MS = 3_000;

export type PendingLevel = 'checking' | 'slow' | 'very-slow';

/** Mức chờ khi chưa có chữ: ≥10 s slow, ≥45 s very-slow (không tự huỷ). */
export const pendingLevel = (elapsedMs: number): PendingLevel =>
  elapsedMs >= VERY_SLOW_MS ? 'very-slow' : elapsedMs >= SLOW_MS ? 'slow' : 'checking';

/** Thông báo `#chat-status` khi nhận `done`. */
export function doneStatus(turn: Pick<ChatTurn, 'trace' | 'sources'>): string {
  if (answerOutcome(turn.trace).kind === 'number-blocked') return t('status.blockedNum');
  const n = turn.sources?.length ?? 0;
  return n ? t('status.done', { n }) : t('status.doneNoSource');
}
