import React from 'react';
import { formatTrace } from './trace';

const agentStyles: [RegExp, string][] = [
  [/rule/i, 'rule'], [/knowledge graph|graph/i, 'graph'], [/knowledge/i, 'know'], [/predict/i, 'pred'],
  [/learning/i, 'learn'], [/response/i, 'resp'], [/conversation/i, 'conv'], [/coordinator/i, 'coord']
];

export function TracePipeline({ trace, hideTitle }: { trace: string[]; hideTitle?: boolean }) {
  const steps = formatTrace(trace);
  return (
    <div className="pipeline">
      {!hideTitle && <div className="trace-title">Luồng xử lý của hệ đa tác tử ({steps.length} bước)</div>}
      <ol className="pipeline-steps" aria-label="Các bước tác tử đã xử lý câu trả lời">
        {steps.map((step, i) => {
          const cls = agentStyles.find(([re]) => re.test(step.name))?.[1] || 'other';
          return (
            <li key={i} className={`pstep pstep-${cls}${step.blocked ? ' pstep-blocked' : ''}`}>
              <span className="pstep-no">{i + 1}</span>
              <span className="pstep-body"><strong>{step.name}</strong>{step.detail && <small>{step.detail}</small>}</span>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
