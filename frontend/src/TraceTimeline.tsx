/** SCR-1.C6: các bước xử lý đã gộp theo agent (design 2c). */
import React, { forwardRef } from 'react';
import { t } from './copy.ts';
import { groupTrace, type AnswerOutcome, type StepStatus } from './trace.ts';
import { outcomeCounts } from './AnswerOutcome';

const ICONS: Record<StepStatus, string> = { ok: '✓', skip: '–', warn: '!', blocked: '✕', none: '' };

/** Lớp màu theo agent – dùng chung với `.pstep-*` của SCR-4. */
export function agentClass(name: string): string {
  const pairs: [RegExp, string][] = [
    [/rule/i, 'rule'], [/graph/i, 'graph'], [/knowledge/i, 'know'], [/predict/i, 'pred'],
    [/learning/i, 'learn'], [/response/i, 'resp'], [/conversation/i, 'conv'], [/coordinator/i, 'coord']
  ];
  return pairs.find(([re]) => re.test(name))?.[1] ?? 'other';
}

type Props = { trace: string[]; outcome: AnswerOutcome; defaultOpen: boolean; onGoData: (anchor: string) => void };

export const TraceTimeline = forwardRef<HTMLDetailsElement, Props>(function TraceTimeline({ trace, outcome, defaultOpen, onGoData }, ref) {
  const steps = groupTrace(trace);
  const summary = [t('trace.summary', { steps: steps.length }), ...outcomeCounts(outcome)].join(' · ');
  return (
    <details className="chat-trace" open={defaultOpen} ref={ref}>
      <summary>{summary}</summary>
      <p className="trace-intro">{t('trace.intro')}</p>
      <ol className="timeline" aria-label={t('trace.listLabel')}>
        {steps.map((s, i) => (
          <li key={i} className={`tstep pstep-${agentClass(s.name)} tstep-${s.status}`}>
            {ICONS[s.status] && <span className="tstep-icon" aria-hidden="true">{ICONS[s.status]}</span>}
            <span className="tstep-body">
              <strong>{s.label}</strong>
              {s.subtitle && <small className="tstep-sub">{s.subtitle}</small>}
              {s.details.map((d, j) => <span key={j} className="tstep-detail">{d}</span>)}
            </span>
          </li>
        ))}
      </ol>
      <button type="button" className="linkbutton trace-more" onClick={() => onGoData('data-assistant')}>{t('trace.more')} →</button>
    </details>
  );
});
