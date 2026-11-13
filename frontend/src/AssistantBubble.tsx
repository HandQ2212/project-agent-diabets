/** Một lượt trả lời của trợ lý (SCR-1), hiển thị theo `answerOutcome` – design-ui.md 3a-1. */
import React, { useRef } from 'react';
import type { ChatTurn } from './types';
import { t } from './copy.ts';
import { answerOutcome, stripRemovedNote } from './trace.ts';
import { OutcomeSummary, BlockedNumberCard, SafetyCard } from './AnswerOutcome';
import { TraceTimeline } from './TraceTimeline';
import { SourceGroups, revealSource } from './SourceGroups';
import { CitedText } from './CitedText';

type Props = {
  turn: ChatTurn;
  index: number;
  /** Lượt đang stream (chưa `done`, chưa lỗi/dừng). */
  streaming: boolean;
  /** Mở C6 sẵn cho lượt trả lời mới nhất. */
  traceOpen: boolean;
  /** Hiện nút Thử lại cho lượt lỗi cuối khi không bận. */
  canRetry: boolean;
  onRetry: () => void;
  /** "Hỏi lại cách khác": điền lại câu hỏi của lượt này, không tự gửi. */
  onAskAgain: () => void;
  onGoData: (anchor: string) => void;
  onStatus: (message: string) => void;
};

export function AssistantBubble({ turn, index, streaming, traceOpen, canRetry, onRetry, onAskAgain, onGoData, onStatus }: Props) {
  const traceRef = useRef<HTMLDetailsElement>(null);
  const finished = !!turn.done && !turn.error;
  const outcome = answerOutcome(finished ? turn.trace : undefined);
  const sources = turn.sources ?? [];
  const kind = finished ? outcome.kind : null;

  const openTrace = () => {
    const d = traceRef.current;
    if (!d) return;
    d.open = true;
    d.querySelector('summary')?.focus();
  };
  const cite = (n: number) => {
    if (revealSource(index, n)) onStatus(t('status.cite', { n }));
  };

  const body = finished ? stripRemovedNote(turn.content, outcome) : turn.content;
  const bubbleCls = ['chat-bubble', turn.error ? 'chat-error' : '', kind === 'rule-blocked' ? 'chat-safety' : ''].filter(Boolean).join(' ');

  let main: React.ReactNode;
  if (kind === 'rule-blocked') main = <SafetyCard outcome={outcome} text={turn.content} />;
  else if (kind === 'number-blocked') main = <BlockedNumberCard unsupported={outcome.unsupported ?? []} rawText={turn.content} onRetry={onAskAgain} />;
  else if (body) main = finished && sources.length ? <CitedText text={body} sourceCount={sources.length} onCite={cite} /> : <div className="chat-text">{body}</div>;

  const showSources = finished && kind !== 'rule-blocked' && kind !== 'conversation';
  const disclaimer = finished && kind !== 'rule-blocked' && kind !== 'number-blocked';

  return (
    <div className="chat-row assistant">
      <span className="chat-avatar" aria-hidden="true">✳</span>
      <div className={bubbleCls}>
        {main}
        {turn.stopped && <small className="chat-stopped">{t('chat.stopped')}</small>}
        {turn.error && (
          <div className="chat-error-msg">
            <span>{turn.error}</span>
            {canRetry && <button type="button" className="chat-retry" onClick={onRetry}>Thử lại</button>}
          </div>
        )}
        {finished && !!turn.trace?.length && <OutcomeSummary outcome={outcome} onOpenTrace={openTrace} onGoData={onGoData} />}
        {showSources && <SourceGroups sources={sources} turnIndex={index} facts={outcome.facts} webOpen={kind === 'links-only'} />}
        {finished && !!turn.trace?.length && <TraceTimeline ref={traceRef} trace={turn.trace} outcome={outcome} defaultOpen={traceOpen} onGoData={onGoData} />}
        {disclaimer && <small className="chat-disclaimer">{t('chat.disclaimer')}</small>}
        {streaming && turn.content !== '' && <small className="chat-writing" aria-hidden="true">{t('pending.writing')}</small>}
      </div>
    </div>
  );
}
