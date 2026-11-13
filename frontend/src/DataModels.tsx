/** SCR-2 "Dữ liệu và mô hình" (design-ui.md 2d, 3a-2, 4b, 6c). Số liệu luôn đọc từ `/api/about`, không hard-code. */
import React, { useEffect, useLayoutEffect, useState } from 'react';
import type { HealthStatus } from './types';
import { t, relLabel } from './copy.ts';
import { fmtDec, fmtPct, fmtInt, fmtDateVN, fmtDateTimeVN, publisherFromTitle, PUBLISHERS } from './format.ts';
import {
  fetchAbout, kbDown, missingMetrics, filterSources, FILTER_OTHER,
  type AboutInfo, type AboutResult, type ModelInfo, type AssistantInfo, type KbInfo, type RlInfo
} from './about.ts';

type Kind = 'symptoms' | 'brfss' | 'nhanes_research' | 'nhanes15_research';
const KINDS: Kind[] = ['symptoms', 'brfss', 'nhanes_research', 'nhanes15_research'];

type Props = {
  health: HealthStatus | null | undefined;
  /** id cần cuộn tới + focus sau khi tải (`data-kb`, `data-assistant`, `model-<kind>`…). */
  anchor?: string;
  onAnchorDone: () => void;
  onTryModel: (kind: Kind) => void;
  onAsk: () => void;
};

type Load = { state: 'loading' } | AboutResult;

/** Chế độ dev: `?about=fixture|fixture-kbdown|fixture-partial|404|error|loading` để chụp đủ trạng thái khi chưa có endpoint. */
async function loadAbout(signal: AbortSignal): Promise<AboutResult | null> {
  if (import.meta.env.DEV) {
    const mode = new URLSearchParams(window.location.search).get('about');
    if (mode === '404') return { state: 'not-ready' };
    if (mode === 'error') return { state: 'error' };
    if (mode === 'loading') return null;
    if (mode?.startsWith('fixture')) {
      const { aboutFixtureVariant } = await import('./about.fixture.ts');
      return { state: 'ok', data: aboutFixtureVariant(mode.replace(/^fixture-?/, '')) };
    }
  }
  return fetchAbout(signal);
}

function Heading({ id, children }: { id: string; children: React.ReactNode }) {
  return <h2 id={id} tabIndex={-1}>{children}</h2>;
}

const TOC = [
  ['data-models', 'data.toc.models'], ['data-assistant', 'data.assistant.title'], ['data-kb', 'data.toc.kb'],
  ['data-sources', 'data.toc.sources'], ['data-limits', 'data.limits.title']
] as const;

export function focusSection(id: string) {
  const el = document.getElementById(id);
  if (!el) return false;
  let target: HTMLElement = el;
  if (el.tagName === 'DETAILS') {
    (el as HTMLDetailsElement).open = true;
    target = el.querySelector('summary') ?? el;
  }
  target.scrollIntoView({ block: 'start' });
  target.focus({ preventScroll: true });
  return true;
}

export function DataModels({ health, anchor, onAnchorDone, onTryModel, onAsk }: Props) {
  const [load, setLoad] = useState<Load>({ state: 'loading' });
  const [reloadKey, setReloadKey] = useState(0);
  const [status, setStatus] = useState('');

  useEffect(() => {
    const ctrl = new AbortController();
    setLoad({ state: 'loading' });
    const slow = window.setTimeout(() => setStatus(t('data.loading')), 1000);
    loadAbout(ctrl.signal).then(r => {
      window.clearTimeout(slow);
      if (r) { setLoad(r); setStatus(''); }
    }).catch(() => { /* bị huỷ khi rời trang */ });
    return () => { ctrl.abort(); window.clearTimeout(slow); };
  }, [reloadKey]);

  useLayoutEffect(() => {
    if (!anchor || load.state === 'loading') return;
    focusSection(anchor);
    onAnchorDone();
  }, [anchor, load.state, onAnchorDone]);

  const reload = () => setReloadKey(k => k + 1);
  const busy = load.state === 'loading';

  return (
    <div className="panel data-page" aria-busy={busy}>
      <p className="sr-only" role="status">{status}</p>
      {busy && <Skeleton />}
      {load.state === 'error' && (
        <div className="outcome-box outcome-notice data-banner" role="alert">
          <p>{t('data.error.load')}</p>
          <button type="button" className="chat-retry" onClick={reload}>{t('common.reload')}</button>
        </div>
      )}
      {load.state === 'not-ready' && (
        <>
          <div className="outcome-box outcome-info data-banner">{t('data.error.notReady')}</div>
          <AssistantStack assistant={null} health={health} onAsk={onAsk} />
          <section className="data-section" aria-labelledby="data-kb">
            <Heading id="data-kb">{t('data.kb.title')}</Heading>
            {health?.services?.neo4j === false && <p className="outcome-box outcome-notice">{t('data.kb.down')}</p>}
          </section>
          <KnownLimits about={null} />
        </>
      )}
      {load.state === 'ok' && <AboutView about={load.data} health={health} onReload={reload} onTryModel={onTryModel} onAsk={onAsk} onStatus={setStatus} />}
    </div>
  );
}

function Skeleton() {
  return (
    <div className="data-skeleton" aria-hidden="true">
      <div className="sk-block">{[0, 1, 2, 3, 4].map(i => <div key={i} className="sk-row" />)}</div>
      <div className="sk-block sk-dl" />
      <div className="sk-block sk-dl" />
    </div>
  );
}

function AboutView({ about, health, onReload, onTryModel, onAsk, onStatus }: {
  about: AboutInfo; health: HealthStatus | null | undefined; onReload: () => void;
  onTryModel: (k: Kind) => void; onAsk: () => void; onStatus: (s: string) => void;
}) {
  const models = about.models ?? [];
  return (
    <>
      {about.generated_at && (
        <p className="data-generated">
          {t('data.generatedAt', { time: fmtDateTimeVN(about.generated_at) })}{' '}
          <button type="button" className="linkbutton" onClick={onReload}>{t('common.reload')}</button>
        </p>
      )}
      <nav className="data-toc" aria-label={t('data.toc.label')}>
        <ul>{TOC.map(([id, key]) => <li key={id}><a href={`#${id}`} onClick={e => { e.preventDefault(); focusSection(id); }}>{t(key)}</a></li>)}</ul>
      </nav>

      <section className="data-section" aria-labelledby="data-models">
        <Heading id="data-models">{t('data.models.title', { n: models.length })}</Heading>
        {models.length ? <ModelTable models={models} /> : <p>{t('data.models.empty')}</p>}
        <details className="data-help">
          <summary>{t('data.models.help')}</summary>
          <p>{t('data.models.helpBody')}</p>
        </details>
        {models.map(m => <ModelDetails key={m.kind} model={m} onTry={KINDS.includes(m.kind as Kind) ? () => onTryModel(m.kind as Kind) : undefined} />)}
      </section>

      <RlSummary rl={about.rl ?? null} />
      <AssistantStack assistant={about.assistant ?? null} health={health} onAsk={onAsk} />
      <KbSection kb={kbDown(about) ? null : about.kb!} />
      {!kbDown(about) && <ReviewedSources kb={about.kb!} onStatus={onStatus} />}
      <KnownLimits about={about} />
    </>
  );
}

function ModelTable({ models }: { models: ModelInfo[] }) {
  const caption = t('data.models.caption');
  return (
    <div className="table-scroll" tabIndex={0} role="region" aria-label={caption}>
      <table className="data-table model-table">
        <caption>{caption}</caption>
        <thead>
          <tr>
            <th scope="col">{t('data.models.col.name')}</th>
            <th scope="col">{t('data.models.col.arch')}</th>
            <th scope="col" className="num">{t('data.models.col.auc')}</th>
            <th scope="col" className="num">{t('data.models.col.f1')}</th>
            <th scope="col" className="num">{t('data.models.col.recall')}</th>
            <th scope="col" className="num">{t('data.models.col.precision')}</th>
            <th scope="col" className="num">{t('data.models.col.base')}</th>
          </tr>
        </thead>
        <tbody>
          {models.map(m => {
            const x = m.metrics_test;
            return (
              <tr key={m.kind}>
                <th scope="row">{m.name}{missingMetrics(m) && <small className="cell-note">{t('data.models.missing')}</small>}</th>
                <td>{m.architecture ?? '—'}</td>
                <td className="num">{fmtDec(x?.roc_auc)}</td>
                <td className="num">{fmtDec(x?.f1_pos)}</td>
                <td className="num">{fmtDec(x?.recall_pos)}</td>
                <td className="num">{fmtDec(x?.precision_pos)}</td>
                <td className="num">{fmtPct(m.dataset?.positive_rate_test)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function ModelDetails({ model: m, onTry }: { model: ModelInfo; onTry?: () => void }) {
  const d = m.dataset;
  const x = m.metrics_test;
  const cm = x?.confusion_matrix;
  const split = [d?.n_train, d?.n_validation, d?.n_test];
  return (
    <details className="model-details" id={`model-${m.kind}`}>
      <summary>{t('data.models.details', { name: m.name })}</summary>
      <dl className="data-dl">
        {d?.name && <><dt>{t('data.model.dataset')}</dt><dd>{d.name}{d.cycles?.length ? ` (${d.cycles.join(', ')})` : ''}</dd></>}
        {d?.label && <><dt>{t('data.model.label')}</dt><dd>{d.label}</dd></>}
        {split.some(v => v != null) && <><dt>{t('data.model.split')}</dt><dd>{split.map(fmtInt).join(' / ')}</dd></>}
        {m.threshold != null && <><dt>{t('data.model.threshold')}</dt><dd>{m.threshold.toLocaleString('vi-VN')}{m.selection_rule ? ` · ${m.selection_rule}` : ''}</dd></>}
        {m.baseline && (
          <><dt>{t('data.model.baseline')}</dt>
            <dd>{m.baseline.name}: ROC-AUC {fmtDec(m.baseline.roc_auc)}{m.baseline.f1_pos != null ? `, F1 ${fmtDec(m.baseline.f1_pos)}` : ''}{m.baseline.split ? ` (${m.baseline.split})` : ''}</dd></>
        )}
        {x?.accuracy != null && <><dt>{t('data.model.accuracy')}</dt><dd>{fmtDec(x.accuracy)}<small className="cell-note">{t('data.metric.accuracyNote')}</small></dd></>}
        {!!m.limitations?.length && <><dt>{t('data.model.limits')}</dt><dd><ul>{m.limitations.map(l => <li key={l}>{l}</li>)}</ul></dd></>}
      </dl>
      {missingMetrics(m) && <p className="cell-note">{t('data.models.missing')}</p>}
      {cm && cm.length === 2 && cm[0]?.length === 2 && (
        <table className="data-table confusion">
          <caption>{t('data.model.confusion')}</caption>
          <thead><tr><td /><th scope="col">{t('data.cm.predNeg')}</th><th scope="col">{t('data.cm.predPos')}</th></tr></thead>
          <tbody>
            <tr><th scope="row">{t('data.cm.actualNeg')}</th><td className="num">{fmtInt(cm[0][0])}</td><td className="num">{fmtInt(cm[0][1])}</td></tr>
            <tr><th scope="row">{t('data.cm.actualPos')}</th><td className="num">{fmtInt(cm[1][0])}</td><td className="num">{fmtInt(cm[1][1])}</td></tr>
          </tbody>
        </table>
      )}
      {onTry && <button type="button" className="chat-retry" onClick={onTry}>{t('data.model.try')} →</button>}
    </details>
  );
}

function RlSummary({ rl }: { rl: RlInfo | null }) {
  return (
    <section className="data-section" aria-labelledby="data-rl">
      <Heading id="data-rl">{t('data.rl.title')}</Heading>
      {!rl?.results?.length ? <p>{t('data.rl.missing')}</p> : (
        <>
          <table className="data-table">
            <caption>{t('data.rl.caption', { episodes: rl.episodes_per_seed ?? '—' })}</caption>
            <tbody>
              {rl.results.map(r => (
                <tr key={r.policy}><th scope="row">{r.policy}</th><td className="num">{fmtDec(r.mean_return, 2)}</td></tr>
              ))}
            </tbody>
          </table>
          <p className="cell-note">{t('data.rl.note')}</p>
        </>
      )}
    </section>
  );
}

function AssistantStack({ assistant: a, health, onAsk }: { assistant: AssistantInfo | null; health: HealthStatus | null | undefined; onAsk: () => void }) {
  const llmUp = health?.services?.ollama;
  return (
    <section className="data-section" aria-labelledby="data-assistant">
      <Heading id="data-assistant">{t('data.assistant.title')}</Heading>
      <dl className="data-dl">
        <dt>{t('data.assistant.llm')}</dt>
        <dd>
          {a?.llm ? `${a.llm}${a.llm_provider ? ` (${a.llm_provider})` : ''}` : '—'}
          {llmUp !== undefined && (
            <span className="svc"><span className={`status-dot ${llmUp ? 'online' : 'offline'}`} aria-hidden="true" /> {t(llmUp ? 'data.llm.running' : 'data.llm.down')}</span>
          )}
        </dd>
        {a?.embedding && <><dt>{t('data.assistant.embed')}</dt><dd>{a.embedding}{a.embedding_dim ? ` (${t('data.assistant.dim', { n: a.embedding_dim })})` : ''}</dd></>}
        {a?.top_k != null && a.min_cosine != null && (
          <><dt>{t('data.assistant.retrieval')}</dt><dd>{t('data.assistant.retrievalValue', { k: a.top_k, min: a.min_cosine.toLocaleString('vi-VN') })}</dd></>
        )}
        <dt>{t('data.assistant.rule')}</dt><dd>{t('data.assistant.ruleValue')}</dd>
        <dt>{t('data.assistant.guard')}</dt><dd>{t('data.assistant.guardValue')}</dd>
      </dl>
      <button type="button" className="linkbutton" onClick={onAsk}>{t('data.assistant.ask')} →</button>
    </section>
  );
}

function KbSection({ kb }: { kb: KbInfo | null }) {
  return (
    <section className="data-section" aria-labelledby="data-kb">
      <Heading id="data-kb">{t('data.kb.title')}</Heading>
      {!kb ? <p className="outcome-box outcome-notice">{t('data.kb.down')}</p> : (
        <>
          <dl className="stat-tiles">
            {([
              ['reviewed_chunks', 'data.kb.reviewedChunks'], ['reviewed_docs', 'data.kb.reviewedDocs'],
              ['web_chunks', 'data.kb.webChunks'], ['web_pages', 'data.kb.webPages'],
              ['topics', 'data.kb.topics'], ['entities', 'data.kb.entities'], ['relations', 'data.kb.relations']
            ] as const).map(([field, key]) => (
              <div key={field} className="stat-tile"><dt>{t(key)}</dt><dd>{fmtInt(kb[field])}</dd></div>
            ))}
          </dl>
          {!!kb.relations_by_type?.length && (
            <table className="data-table">
              <caption>{t('data.kb.relCaption')}</caption>
              <tbody>{kb.relations_by_type.map(r => <tr key={r.type}><th scope="row">{relLabel(r.type)}</th><td className="num">{fmtInt(r.count)}</td></tr>)}</tbody>
            </table>
          )}
          {!!kb.topic_names?.length && (
            <details className="data-help">
              <summary>{t('data.kb.topicList', { n: kb.topics ?? kb.topic_names.length })}</summary>
              <ul className="topic-list">{kb.topic_names.map(n => <li key={n}>{n}</li>)}</ul>
            </details>
          )}
        </>
      )}
    </section>
  );
}

function ReviewedSources({ kb, onStatus }: { kb: KbInfo; onStatus: (s: string) => void }) {
  const [filter, setFilter] = useState<string | null>(null);
  const list = (kb.reviewed_sources ?? []).map(s => ({ ...s, publisher: s.publisher || publisherFromTitle(s.title, s.url) }));
  const shown = filterSources(list, filter, PUBLISHERS);
  const choose = (f: string | null) => {
    setFilter(f);
    onStatus(t('data.src.count', { n: filterSources(list, f, PUBLISHERS).length }));
  };
  const filters: [string | null, string][] = [[null, t('data.src.all')], ...PUBLISHERS.map(p => [p, p] as [string, string]), [FILTER_OTHER, t('data.src.other')]];
  const filterLabel = filters.find(([f]) => f === filter)?.[1] ?? '';
  return (
    <section className="data-section" aria-labelledby="data-sources">
      <Heading id="data-sources">{t('data.src.title', { n: list.length })}</Heading>
      <div className="tabs" role="group" aria-label={t('data.src.filter')}>
        {filters.map(([f, label]) => (
          <button key={label} type="button" className={filter === f ? 'selected' : ''} aria-pressed={filter === f} onClick={() => choose(f)}>{label}</button>
        ))}
      </div>
      {!shown.length ? (
        <p>{t('data.src.noResults', { publisher: filterLabel })} <button type="button" className="linkbutton" onClick={() => choose(null)}>{t('data.src.clear')}</button></p>
      ) : (
        <table className="data-table src-table">
          <thead><tr>
            <th scope="col">{t('data.src.col.publisher')}</th><th scope="col">{t('data.src.col.title')}</th>
            <th scope="col">{t('data.src.col.topic')}</th><th scope="col">{t('data.src.col.date')}</th>
          </tr></thead>
          <tbody>
            {shown.map(s => (
              <tr key={s.url + s.title}>
                <td><span className="src-badge src-badge-curated">{s.publisher ?? t('data.src.other')}</span></td>
                <td><a href={s.url} target="_blank" rel="noreferrer">{s.title}<span className="sr-only"> {t('src.newTab')}</span> <span aria-hidden="true">↗</span></a></td>
                <td>{s.topic ?? ''}</td>
                <td>{fmtDateVN(s.date)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}

function KnownLimits({ about }: { about: AboutInfo | null }) {
  const docs = about?.kb?.reviewed_docs;
  const fixed = [
    t('data.limits.1'), t('data.limits.2'),
    docs != null ? t('data.limits.3', { reviewedDocs: docs }) : t('data.limits.3', { reviewedDocs: '' }).replace('phạm vi  tài liệu', 'phạm vi các tài liệu'),
    t('data.limits.4'), t('data.limits.5'), t('data.limits.6')
  ];
  return (
    <section className="data-section" aria-labelledby="data-limits">
      <Heading id="data-limits">{t('data.limits.title')}</Heading>
      <ul className="limits">{[...fixed, ...(about?.limitations ?? [])].map(l => <li key={l}>{l}</li>)}</ul>
    </section>
  );
}

