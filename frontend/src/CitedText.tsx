/** SCR-1.C2: biến `[n]` trong câu trả lời thành nút nhảy tới nguồn (design 2b, 4b). */
import React from 'react';
import { t } from './copy.ts';
import { splitCitations } from './format.ts';

type Props = { text: string; sourceCount: number; onCite: (n: number) => void };

export function CitedText({ text, sourceCount, onCite }: Props) {
  const parts = splitCitations(text, sourceCount);
  return (
    <div className="chat-text">
      {parts.map((p, i) =>
        p.kind === 'text' ? <React.Fragment key={i}>{p.text}</React.Fragment> : (
          <button key={i} type="button" className="cite" aria-label={t('cite.a11y', { n: p.n })} onClick={() => onCite(p.n)}>{p.raw}</button>
        )
      )}
    </div>
  );
}
