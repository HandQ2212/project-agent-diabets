/** SCR-1.C3 (kết quả đối chiếu) và SCR-1.C4 (thẻ chặn) – design-ui.md 2b, 3a-1. */
import React from 'react';
import { t, joinNums, type CopyKey } from './copy.ts';
import { needsEmergencyCall, type AnswerOutcome } from './trace.ts';

/** "3 tài liệu · 3 sự kiện đồ thị" – chỉ các số > 0. */
export function outcomeCounts(o: AnswerOutcome): string[] {
  const out: string[] = [];
  if (o.docs) out.push(t('outcome.count.docs', { n: o.docs }));
  if (o.facts) out.push(t('outcome.count.facts', { n: o.facts }));
  return out;
}

type SummaryProps = {
  outcome: AnswerOutcome;
  /** Mở C6 và focus `summary` của nó. */
  onOpenTrace: () => void;
  /** Lối thoát không-AI khi không có nguồn → SCR-2 #data-kb. */
  onGoData: (anchor: string) => void;
};

/** C3: khung thông báo (lược câu / không nguồn / chỉ web) + dòng tóm tắt có link "Các bước xử lý". */
export function OutcomeSummary({ outcome: o, onOpenTrace, onGoData }: SummaryProps) {
  let box: React.ReactNode = null;
  let line: { icon: string; text: string } | null = null;

  switch (o.kind) {
    case 'number-filtered': {
      const vars = { k: o.removed ?? 0, n: o.total ?? 0, nums: joinNums(o.unsupported ?? []) };
      box = (
        <div className="outcome-box outcome-notice">
          <span aria-hidden="true">ⓘ </span>
          {o.unsupported?.length ? t('outcome.filtered', vars) : t('outcome.filtered.noNums', vars)}
        </div>
      );
      line = { icon: '✓', text: t('outcome.verified') };
      break;
    }
    case 'verified':
      line = { icon: '✓', text: t(o.regenerated ? 'outcome.regenerated' : 'outcome.verified') };
      break;
    case 'unchecked':
      line = { icon: '–', text: t('outcome.unchecked') };
      break;
    case 'no-source':
      box = (
        <div className="outcome-box outcome-info">
          <p>{t('outcome.nosource')}</p>
          <button type="button" className="linkbutton" onClick={() => onGoData('data-kb')}>{t('outcome.nosource.link')} →</button>
        </div>
      );
      break;
    case 'links-only':
      box = <div className="outcome-box outcome-info">{t('outcome.linksOnly')}</div>;
      break;
    default:
      return null; // rule-blocked, conversation, number-blocked: không có C3
  }

  const text = [line?.text, ...outcomeCounts(o)].filter(Boolean).join(' · ');
  return (
    <div className="outcome">
      {box}
      <p className="outcome-line">
        {line && <span aria-hidden="true" className="outcome-icon">{line.icon} </span>}
        {text && text + ' · '}
        <button type="button" className="linkbutton" onClick={onOpenTrace}>{t('outcome.traceLink')}</button>
      </p>
    </div>
  );
}

type BlockedNumberProps = { unsupported: string[]; rawText: string; onRetry: () => void };

/** C4 kind `number`: thay thân câu trả lời; thân gốc nằm trong "Xem thông báo đầy đủ". Không Gọi 115. */
export function BlockedNumberCard({ unsupported, rawText, onRetry }: BlockedNumberProps) {
  return (
    <div className="blocked-card outcome-notice">
      <strong className="blocked-title"><span aria-hidden="true">⚠ </span>{t('blockedNum.title')}</strong>
      <p>{unsupported.length ? t('blockedNum.body', { nums: joinNums(unsupported) }) : t('blockedNum.bodyNoNums')}</p>
      <div className="blocked-actions">
        <button type="button" className="chat-retry" onClick={onRetry}>{t('blockedNum.retry')}</button>
        {rawText && (
          <details className="blocked-raw">
            <summary>{t('blockedNum.raw')}</summary>
            <div className="chat-text">{rawText}</div>
          </details>
        )}
      </div>
    </div>
  );
}

const SAFETY_TITLES: Record<string, CopyKey> = {
  EMERGENCY: 'safety.title.emergency',
  MEDICATION_DOSAGE: 'safety.title.dosage',
  PII_SENSITIVE: 'safety.title.pii',
  PROMPT_INJECTION: 'safety.title.injection'
};

/** C4 kind `rule`: tiêu đề theo category; Gọi 115 CHỈ khi EMERGENCY (BUG-2). */
export function SafetyCard({ outcome, text }: { outcome: AnswerOutcome; text: string }) {
  const titleKey = SAFETY_TITLES[outcome.category ?? ''] ?? 'safety.title.other';
  return (
    <>
      <strong className="chat-safety-title">{t(titleKey)}</strong>
      {text && <div className="chat-text">{text}</div>}
      {needsEmergencyCall(outcome) && <a className="chat-call" href="tel:115">{t('safety.call')}</a>}
      <small className="chat-safety-note">{t('safety.note')}</small>
    </>
  );
}
