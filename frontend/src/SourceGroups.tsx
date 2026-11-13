/** SCR-1.C5: nguồn chia 3 nhóm, giữ số [n] gốc (design 2b). */
import React from 'react';
import type { Source } from './types';
import { t, relLabel } from './copy.ts';
import { fmtDateVN, safeHref } from './format.ts';
import { groupSources, type SourceItem } from './sourceGrouping.ts';

export const sourceDomId = (turnIndex: number, n: number) => `src-${turnIndex}-${n}`;

type Props = { sources: Source[]; turnIndex: number; facts?: number; webOpen: boolean };

function Note({ item, kind, facts }: { item: SourceItem; kind: 'reviewed' | 'graph' | 'web'; facts?: number }) {
  const s = item.source;
  let note: string;
  if (kind === 'reviewed') note = s.topic ? t('src.note.reviewed', { topic: s.topic }) : t('src.note.reviewed', { topic: '' }).replace(/ · $/, '');
  else if (kind === 'graph') {
    const n = s.facts?.length || facts;
    note = n ? t('src.note.graph', { facts: n }) : t('src.note.graphNoCount');
  } else note = s.fetched_at ? t('src.note.web', { date: fmtDateVN(s.fetched_at) }) : t('src.note.web', { date: '' }).replace(' ngày ,', ','); // không có ngày: bỏ cụm "ngày {date}"
  return (
    <small>
      {note}
      {item.sameAs !== undefined ? ' · ' + t('src.sameLink', { k: item.sameAs }) : ''}
    </small>
  );
}

function Item({ item, kind, turnIndex, facts }: { item: SourceItem; kind: 'reviewed' | 'graph' | 'web'; turnIndex: number; facts?: number }) {
  const badge = kind === 'reviewed' ? item.publisher || t('src.badge.reviewed') : kind === 'graph' ? t('src.badge.graph') : t('src.badge.web');
  const badgeCls = kind === 'reviewed' ? 'curated' : kind;
  return (
    <li id={sourceDomId(turnIndex, item.n)} tabIndex={-1} className={`src src-${badgeCls}`}>
      <span className={`src-badge src-badge-${badgeCls}`}>{badge}</span>
      {safeHref(item.source.url) ? (
        <a href={safeHref(item.source.url)!} target="_blank" rel="noreferrer">
          [{item.n}] {item.title}<span className="sr-only"> {t('src.newTab')}</span> <span aria-hidden="true">↗</span>
        </a>
      ) : <span className="src-nolink">[{item.n}] {item.title}</span>}
      <Note item={item} kind={kind} facts={facts} />
      {kind === 'graph' && !!item.source.facts?.length && (
        <ul className="src-facts">
          {item.source.facts.slice(0, 5).map((f, i) => (
            <li key={i}>{f.from} —{relLabel(f.type)}→ {f.to}{f.threshold != null && f.threshold !== '' ? ` (${f.threshold})` : ''}</li>
          ))}
        </ul>
      )}
    </li>
  );
}

export function SourceGroups({ sources, turnIndex, facts, webOpen }: Props) {
  const groups = groupSources(sources);
  if (!groups.length) return null;
  return (
    <div className="chat-sources src-groups">
      {groups.map(g => {
        const list = <ul className="source-list">{g.items.map(it => <Item key={it.n} item={it} kind={g.kind} turnIndex={turnIndex} facts={facts} />)}</ul>;
        if (g.kind === 'web') {
          return (
            <details key="web" className="src-group src-group-web" open={webOpen || undefined}>
              <summary>{t('src.group.web', { n: g.items.length })}</summary>
              {list}
            </details>
          );
        }
        return (
          <section key={g.kind} className="src-group">
            <strong className="src-group-title">{t(g.kind === 'reviewed' ? 'src.group.reviewed' : 'src.group.graph', { n: g.items.length })}</strong>
            {list}
          </section>
        );
      })}
    </div>
  );
}

/**
 * Nhảy tới nguồn n của lượt turnIndex: mở nhóm đang đóng, focus, cuộn, nháy viền 1,5 s (bỏ khi reduced-motion).
 * Trả về true nếu tìm thấy.
 */
export function revealSource(turnIndex: number, n: number): boolean {
  const el = document.getElementById(sourceDomId(turnIndex, n));
  if (!el) return false;
  const details = el.closest('details');
  if (details && !details.open) details.open = true;
  el.focus({ preventScroll: true });
  el.scrollIntoView({ block: 'nearest' });
  if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    el.classList.add('src-flash');
    window.setTimeout(() => el.classList.remove('src-flash'), 1500);
  }
  return true;
}
