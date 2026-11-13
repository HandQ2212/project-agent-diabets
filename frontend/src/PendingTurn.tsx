/**
 * SCR-1.C1: lượt đang chờ chữ đầu tiên (design 2b, 3a-1, Q3).
 * Backend chưa phát sự kiện `stage` nên KHÔNG giả tiến độ: các bước chỉ là danh sách "sẽ chạy", không tick.
 * Thông báo cho screen reader đi qua `#chat-status` của trang cha (container này aria-hidden).
 */
import React, { useEffect, useRef, useState } from 'react';
import { t } from './copy.ts';
import { pendingLevel, SHOW_ELAPSED_MS } from './chatState.ts';

type Props = {
  /** `performance.now()` lúc gửi. */
  startedAt: number;
  /** Gọi đúng 1 lần khi vượt 10 s (trang cha đọc `status.slow`). */
  onSlow?: () => void;
};

export function PendingTurn({ startedAt, onSlow }: Props) {
  const [now, setNow] = useState(() => performance.now());
  const slowSent = useRef(false);

  useEffect(() => {
    const id = window.setInterval(() => setNow(performance.now()), 1000);
    return () => window.clearInterval(id);
  }, []);

  const elapsed = Math.max(0, now - startedAt);
  const level = pendingLevel(elapsed);

  useEffect(() => {
    if (level !== 'checking' && !slowSent.current) {
      slowSent.current = true;
      onSlow?.();
    }
  }, [level, onSlow]);

  const steps = ['pending.step.safety', 'pending.step.retrieve', 'pending.step.write', 'pending.step.check'] as const;
  return (
    <div className="chat-row assistant">
      <span className="chat-avatar" aria-hidden="true">✳</span>
      <div className="chat-bubble pending" aria-hidden="true">
        <div className="pending-head">
          <strong><span className="pending-dot" />{t('pending.title')}</strong>
          {elapsed >= SHOW_ELAPSED_MS && <span className="pending-elapsed"> · {t('pending.elapsed', { s: Math.floor(elapsed / 1000) })}</span>}
        </div>
        <ol className="pending-steps">
          {steps.map(k => <li key={k}><span className="pending-bullet">○</span>{t(k)}</li>)}
        </ol>
        {level === 'slow' && <p className="pending-hint">{t('pending.slow')}</p>}
        {level === 'very-slow' && <p className="pending-hint">{t('pending.verySlow')}</p>}
      </div>
    </div>
  );
}
