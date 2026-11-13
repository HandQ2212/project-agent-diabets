import React, { useState, useEffect, useRef } from 'react';
import { createRoot } from 'react-dom/client';
import './style.css';
import type { Answer, ChatTurn, HealthStatus } from './types';
import { friendlyError, chatErrorMessage, postApi, readDetail, HttpError, StreamInterrupted, StreamFailed } from './api';
import { TracePipeline } from './TracePipeline';
import { SourceList } from './SourceList';
import { Architecture } from './Architecture';
import { AssistantBubble } from './AssistantBubble';
import { doneStatus } from './chatState.ts';
import { NdjsonEventReader, type StreamEvent } from './stream.ts';
import { PendingTurn } from './PendingTurn';
import { DataModels } from './DataModels';
import { t } from './copy.ts';
import { nhanes15Groups, nhanesBasicFields, fieldHint, type NumberField } from './formSpec';

const symptoms: [string, string, string][] = [
  ['polyuria', 'Đi tiểu nhiều (Polyuria)', 'Đi tiểu thường xuyên hơn bình thường, đặc biệt vào ban đêm'],
  ['polydipsia', 'Khát nước nhiều (Polydipsia)', 'Cảm giác khô miệng và khát nước liên tục dù uống nhiều'],
  ['sudden_weight_loss', 'Sụt cân đột ngột', 'Giảm cân nhanh chóng không rõ lý do trong thời gian ngắn'],
  ['weakness', 'Mệt mỏi suy nhược', 'Cảm giác kiệt sức, uể oải kéo dài không hồi phục khi nghỉ ngơi'],
  ['polyphagia', 'Ăn nhiều / Nhanh đói (Polyphagia)', 'Cảm giác đói cồn cào liên tục dù vừa ăn xong'],
  ['genital_thrush', 'Nhiễm nấm sinh dục', 'Ngứa ngáy, khó chịu hoặc viêm nhiễm nấm tái diễn'],
  ['visual_blurring', 'Nhìn mờ thoáng qua', 'Thị lực giảm sút, mắt mờ không ổn định'],
  ['itching', 'Ngứa da toàn thân', 'Khô ngứa râm ran trên da khó chịu'],
  ['irritability', 'Dễ cáu gắt / Thay đổi tâm trạng', 'Tâm trạng thất thường, dễ bực bội, khó chịu'],
  ['delayed_healing', 'Vết thương lâu lành', 'Vết trầy xước, đứt tay hoặc loét mất nhiều tuần mới khỏi'],
  ['partial_paresis', 'Yếu cơ / Liệt nhẹ', 'Cảm giác yếu sức ở một nhóm cơ hoặc bàn tay, bàn chân'],
  ['muscle_stiffness', 'Cứng cơ', 'Căng cứng các cơ, đặc biệt khi thức dậy vào buổi sáng'],
  ['alopecia', 'Rụng tóc', 'Tóc rụng nhiều bất thường từng mảng hoặc rải rác'],
  ['obesity', 'Béo phì / Thừa cân', 'Thừa cân rõ rệt hoặc vòng bụng lớn']
];

const brfssOptions: Record<string, [string, string][]> = {
  _AGEG5YR: [
    ['1', '18–24 tuổi'],
    ['2', '25–29 tuổi'],
    ['3', '30–34 tuổi'],
    ['4', '35–39 tuổi'],
    ['5', '40–44 tuổi'],
    ['6', '45–49 tuổi'],
    ['7', '50–54 tuổi'],
    ['8', '55–59 tuổi'],
    ['9', '60–64 tuổi'],
    ['10', '65–69 tuổi'],
    ['11', '70–74 tuổi'],
    ['12', '75–79 tuổi'],
    ['13', '80 tuổi trở lên']
  ],
  SEXVAR: [
    ['1', 'Nam'],
    ['2', 'Nữ']
  ],
  _SMOKER3: [
    ['1', 'Hút thuốc hằng ngày'],
    ['2', 'Hút thuốc một số ngày'],
    ['3', 'Đã từng hút nhưng đã bỏ'],
    ['4', 'Chưa từng hút thuốc']
  ],
  _TOTINDA: [
    ['1', 'Có (vận động ngoài giờ làm việc)'],
    ['2', 'Không (chủ yếu tĩnh tại)']
  ]
};

const brfssLabels: Record<string, { label: string; hint: string }> = {
  _AGEG5YR: { label: 'Nhóm tuổi (BRFSS CDC)', hint: 'Phân nhóm 5 năm theo chuẩn khảo sát y tế BRFSS' },
  SEXVAR: { label: 'Giới tính sinh học', hint: 'Theo khai báo trong khảo sát y tế' },
  _SMOKER3: { label: 'Tình trạng hút thuốc', hint: 'Đã hút ít nhất 100 điếu thuốc trong đời và mức độ hiện tại' },
  _TOTINDA: { label: 'Hoạt động thể chất (30 ngày qua)', hint: 'Có tham gia bài tập, đi bộ, chạy hoặc thể thao ngoài giờ làm' }
};

const views = [
  ['home', 'Tổng quan'],
  ['risk', 'Đánh giá mô hình'],
  ['chat', 'Hỏi đáp'],
  ['rl', 'Mô phỏng RL'],
  ['arch', 'Kiến trúc hệ thống'],
  ['data', t('nav.data')]
] as const;

const starterQuestions = [
  'Những triệu chứng cảnh báo điển hình của đái tháo đường là gì?',
  'Người bệnh đái tháo đường cần lưu ý điều gì khi chăm sóc bàn chân?',
  'Khuyến nghị về thời gian vận động thể lực mỗi tuần là bao nhiêu?',
  'Phương pháp đĩa ăn đái tháo đường của ADA phân chia ra sao?'
];

type View = 'home' | 'risk' | 'chat' | 'rl' | 'arch' | 'data';
type Kind = 'symptoms' | 'brfss' | 'nhanes_research' | 'nhanes15_research';

const datasetTabs: [Kind, string][] = [
  ['nhanes15_research', 'NHANES đầy đủ (15 chỉ số)'],
  ['nhanes_research', 'NHANES rút gọn (4 chỉ số)'],
  ['brfss', 'BRFSS (khảo sát lối sống)'],
  ['symptoms', 'UCI (triệu chứng)']
];

const MSG_OLLAMA_DOWN = 'Chưa gửi được vì mô hình ngôn ngữ chưa chạy. Hãy khởi động Ollama rồi tải lại trang.';
const RL_DISCLAIMER = 'Đây là mô phỏng học tập, không phải chỉ định điều trị.';

function healthLabel(h: HealthStatus | null | undefined): { text: string; state: 'loading' | 'online' | 'offline' | 'partial' } {
  if (h === undefined) return { text: 'Đang kiểm tra dịch vụ…', state: 'loading' };
  if (h === null) return { text: 'Không kết nối được máy chủ', state: 'offline' };
  const neo = h.services?.neo4j === false;
  const llm = h.services?.ollama === false;
  if (neo || llm) {
    const names = neo && llm ? 'Neo4j, mô hình ngôn ngữ' : neo ? 'Neo4j' : 'mô hình ngôn ngữ (Ollama)';
    return { text: `Chưa sẵn sàng: ${names}`, state: 'partial' };
  }
  if (h.status === 'ok' && h.services?.neo4j === true && h.services?.ollama === true) return { text: 'Dịch vụ: Trực tuyến', state: 'online' };
  return { text: 'Một số dịch vụ chưa sẵn sàng', state: 'partial' };
}

function App() {
  const [view, setView] = useState<View>('home');
  const [kind, setKind] = useState<Kind>('nhanes15_research');
  const [values, setValues] = useState<Record<string, string>>({});
  const [notice, setNotice] = useState('');
  const [answer, setAnswer] = useState<Answer | null>(null);
  const [question, setQuestion] = useState('');
  const [conversation, setConversation] = useState<ChatTurn[]>([]);
  const [chatStatus, setChatStatus] = useState('');
  const [pendingSince, setPendingSince] = useState(0);
  /** Mục cần cuộn tới khi mở SCR-2 (`data-models`, `data-kb`, `model-<kind>`…). */
  const [dataAnchor, setDataAnchor] = useState<string | undefined>(undefined);
  const chatEnd = useRef<HTMLDivElement>(null);
  const nearBottom = useRef(true);
  const abortRef = useRef<AbortController | null>(null);
  const errorRef = useRef<HTMLDivElement>(null);
  const resultHead = useRef<HTMLHeadingElement>(null);
  const [needs, setNeeds] = useState<number[]>([1, 1, 1, 1]);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [health, setHealth] = useState<HealthStatus | null | undefined>(undefined);
  const hl = healthLabel(health);
  const ollamaDown = health?.services?.ollama === false;

  useEffect(() => {
    fetch('/api/health')
      .then(res => res.json())
      .then(data => setHealth(data))
      .catch(() => setHealth(null));
  }, []);

  // Chỉ cuộn khi có tin nhắn mới hoặc khi kết thúc, và chỉ khi người dùng đang ở gần đáy (không cuộn mỗi token).
  useEffect(() => {
    if (view !== 'chat' || !nearBottom.current) return;
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    chatEnd.current?.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'nearest' });
  }, [conversation.length, busy, view]);

  useEffect(() => {
    if (error && view !== 'chat') errorRef.current?.focus();
  }, [error, view]);

  useEffect(() => {
    if (answer && view !== 'chat') {
      resultHead.current?.focus({ preventScroll: true });
      resultHead.current?.scrollIntoView({ block: 'nearest' });
    }
  }, [answer, view]);

  const reset = (v: View) => {
    setView(v);
    setAnswer(null);
    setError('');
    setNotice('');
  };

  const goData = (anchor?: string) => {
    reset('data');
    setDataAnchor(anchor);
  };

  /** C4 "Hỏi lại cách khác": điền lại câu hỏi, focus ô nhập, đặt con trỏ cuối, không tự gửi. */
  const askAgain = (text: string) => {
    setQuestion(text);
    window.requestAnimationFrame(() => {
      const el = document.getElementById('chat-question') as HTMLTextAreaElement | null;
      if (!el) return;
      el.focus();
      el.setSelectionRange(el.value.length, el.value.length);
    });
  };

  const switchKind = (k: Kind) => {
    if (k === kind) return;
    const hasData = Object.values(values).some(v => v !== '');
    setNotice(hasData ? 'Đã chuyển bộ dữ liệu, các ô đã nhập được xóa.' : '');
    setKind(k);
    setValues({});
    setAnswer(null);
    setError('');
  };

  async function run(path: string, body: unknown) {
    setBusy(true);
    setError('');
    setNotice('');
    setAnswer(null);
    try {
      const res = await postApi(path, body);
      setAnswer(res);
    } catch (e) {
      setError(friendlyError(e));
    } finally {
      setBusy(false);
    }
  }

  function stopChat() {
    abortRef.current?.abort();
  }

  async function sendChat(retry = false) {
    const lastUser = [...conversation].reverse().find(t => t.role === 'user');
    const text = retry ? lastUser?.content ?? '' : question.trim();
    if (busy || ollamaDown || text.length < 2) {
      if (!retry && !busy && !ollamaDown) setError('Vui lòng nhập câu hỏi có ít nhất 2 ký tự.');
      return;
    }
    // Thử lại: bỏ bong bóng lỗi cuối, giữ lượt hỏi; lịch sử gửi đi không gồm chính lượt hỏi đó.
    const base = retry && conversation[conversation.length - 1]?.error !== undefined ? conversation.slice(0, -1) : conversation;
    const prior = retry ? base.slice(0, -1) : base;
    const history = prior.filter(turn => !turn.error && turn.content).slice(-10)
      .map(turn => ({ role: turn.role, content: turn.content.slice(0, 1500) }));
    setConversation(retry ? base : [...base, { role: 'user', content: text }]);
    if (retry) { if (question.trim() === text) setQuestion(''); } else setQuestion('');
    setError('');
    setBusy(true);
    setChatStatus(t('status.start'));
    setPendingSince(performance.now());
    nearBottom.current = true;
    const controller = new AbortController();
    abortRef.current = controller;
    let created = false;
    let started = false;
    const updateAssistant = (append: string | undefined, change: Partial<ChatTurn>) => {
      const exists = created;
      created = true;
      setConversation(current => {
        const last = current[current.length - 1];
        if (exists && last?.role === 'assistant') {
          return [...current.slice(0, -1), { ...last, ...change, content: last.content + (append ?? '') }];
        }
        return [...current, { role: 'assistant', content: append ?? '', ...change }];
      });
    };
    try {
      const response = await fetch('/api/chat/stream', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: text, history }),
        signal: controller.signal
      });
      if (!response.ok || !response.body) throw new HttpError(response.status, await readDetail(response));
      started = true;
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      const events = new NdjsonEventReader();
      let done = false;
      const handle = (event: StreamEvent) => {
        if (event.type === 'delta') {
          if (!created) setChatStatus(t('status.writing'));
          updateAssistant(event.text, {});
        } else if (event.type === 'done') {
          updateAssistant(undefined, { sources: event.sources, trace: event.trace, done: true });
          setChatStatus(doneStatus(event));
          done = true;
        } else {
          throw new StreamFailed();
        }
      };
      while (true) {
        const chunk = await reader.read();
        const text = decoder.decode(chunk.value, { stream: !chunk.done });
        for (const event of events.push(text)) handle(event);
        if (chunk.done) {
          for (const event of events.flush()) handle(event);
          break;
        }
      }
      if (!done) throw new StreamInterrupted();
    } catch (e) {
      if (controller.signal.aborted) {
        if (created) updateAssistant(undefined, { stopped: true });
        else setConversation(current => [...current, { role: 'assistant', content: '', stopped: true }]);
        setChatStatus('');
        document.getElementById('chat-question')?.focus();
      } else {
        const message = chatErrorMessage(e, started, created);
        if (created) updateAssistant(undefined, { error: message });
        else setConversation(current => [...current, { role: 'assistant', content: '', error: message }]);
        setChatStatus('');
        if (!retry) setQuestion(text);
      }
    } finally {
      abortRef.current = null;
      setBusy(false);
    }
  }

  const select = (name: string, choices: [string, string][]) => (
    <select
      required
      value={values[name] || ''}
      onChange={e => setValues({ ...values, [name]: e.target.value })}
    >
      <option value="" disabled>Chọn…</option>
      {choices.map(([v, l]) => (
        <option key={v} value={v}>
          {l}
        </option>
      ))}
    </select>
  );

  const numberField = (x: NumberField) => (
    <label key={x.key}>
      {x.label}
      <small className="field-hint">{fieldHint(x)}</small>
      <input type="number" min={x.min} max={x.max} step={x.step} required value={values[x.key] || ''} onChange={e => setValues({ ...values, [x.key]: e.target.value })} />
    </label>
  );

  const lastTurn = conversation[conversation.length - 1];
  const waiting = busy && (lastTurn?.role !== 'assistant' || (lastTurn.content === '' && !lastTurn.stopped));
  const resultStatus = answer ? (view === 'rl' ? 'Đã có đề xuất chủ đề.' : 'Đã có kết quả.') : '';
  const completed = answer?.status === 'completed';
  const thresholdText = (answer?.threshold ?? 0.5).toLocaleString('vi-VN');

  return (
    <div className="shell">
      <a className="skip-link" href="#main">Bỏ qua điều hướng, đến nội dung chính</a>
      <header>
        <button className="brand" onClick={() => reset('home')}>
          <span className="logo" aria-hidden="true">✳</span>
          <span>
            đường an<small>THÔNG TIN VỀ ĐÁI THÁO ĐƯỜNG</small>
          </span>
        </button>
        <nav aria-label="Điều hướng chính">
          {views.map(([v, l]) => (
            <button
              key={v}
              className={view === v ? 'active' : ''}
              aria-current={view === v ? 'page' : undefined}
              onClick={() => reset(v)}
            >
              {l}
            </button>
          ))}
        </nav>
        <div className="header-status">
          <span className={`status-dot ${hl.state === 'online' ? 'online' : hl.state === 'loading' ? 'checking' : 'offline'}`} aria-hidden="true" />
          <span className="status-text" role="status">{hl.text}</span>
        </div>
      </header>

      <main id="main" tabIndex={-1}>
        {view === 'home' ? (
          <>
            <section className="hero">
              <div>
                <div className="eyebrow">
                  <span /> KIẾN THỨC THAM KHẢO TỪ NGUỒN UY TÍN, DÀNH CHO HỌC TẬP
                </div>
                <h1>
                  Hiểu cơ thể hơn,
                  <br />
                  <em>chăm sóc tốt hơn.</em>
                </h1>
                <p>
                  Tìm hiểu về bệnh đái tháo đường qua những câu trả lời có nguồn tham khảo và các công cụ nghiên cứu dữ liệu.
                </p>
                <div className="actions">
                  <button className="primary" onClick={() => reset('risk')}>
                    Khám phá mô hình đánh giá <span>↗</span>
                  </button>
                  <button className="textbutton" onClick={() => reset('chat')}>
                    Hỏi đáp tri thức <span>→</span>
                  </button>
                </div>
              </div>
              <div className="heroart">
                <div className="art-circle">
                  <span aria-hidden="true">✳</span>
                </div>
                <div className="art-card">
                  <div className="pulse" aria-hidden="true">✦</div>
                  <div>
                    <strong>Kiến thức có nguồn tham khảo.</strong>
                    <small>WHO · CDC · Bộ Y tế VN · ADA</small>
                  </div>
                </div>
                <div className="art-index">01 / CHĂM SÓC CHỦ ĐỘNG</div>
              </div>
            </section>

            <section className="intro">
              <div>
                <div className="eyebrow">KHÁM PHÁ CÁC TÁC TỬ (AGENTS)</div>
                <h2>
                  Hành trình tìm hiểu
                  <br />
                  từng bước một
                </h2>
              </div>
              <p>
                Hệ thống gồm các tác tử: Prediction, Knowledge, Knowledge Graph, Rule, Learning và Response, do Coordinator điều phối.
              </p>
            </section>

            <section className="cards">
              {[
                ['01', 'Đánh giá mô hình', 'Thử nghiệm phân loại trên dữ liệu UCI, BRFSS và NHANES.', 'risk'],
                ['02', 'Hỏi đáp có nguồn', 'Đặt câu hỏi, xem nguồn đi kèm và các bước hệ thống đã xử lý.', 'chat'],
                ['03', 'Mô phỏng RL', 'Tác tử học tăng cường DQN tự động đề xuất lộ trình chủ đề giáo dục phù hợp.', 'rl'],
                ['04', 'Kiến trúc hệ thống', 'Xem các tác tử và dữ liệu nối với nhau như thế nào.', 'arch']
              ].map(([n, t, d, v]) => (
                <button className="feature" key={n} onClick={() => reset(v as View)}>
                  <span className="feature-no">
                    {n} <i aria-hidden="true">↗</i>
                  </span>
                  <h3>{t}</h3>
                  <p>{d}</p>
                </button>
              ))}
            </section>
          </>
        ) : (
          <>
            <div className="pagehead">
              <div className="eyebrow">
                {view === 'data' ? t('data.eyebrow') : <>ĐƯỜNG AN / {view === 'risk' ? 'ĐÁNH GIÁ MÔ HÌNH' : view === 'chat' ? 'HỎI ĐÁP ĐA AGENT' : view === 'arch' ? 'KIẾN TRÚC HỆ THỐNG' : 'MÔ PHỎNG RL'}</>}
              </div>
              <h1>
                {view === 'risk'
                  ? 'Khám phá dữ liệu và mô hình phân loại'
                  : view === 'chat'
                  ? 'Hỏi đáp thông tin y tế có nguồn'
                  : view === 'arch'
                  ? 'Kiến trúc hệ đa tác tử'
                  : view === 'data'
                  ? t('data.title')
                  : 'Học tăng cường điều phối lộ trình học tập'}
              </h1>
              <p>
                {view === 'risk'
                  ? 'Các thí nghiệm phân loại trên dữ liệu UCI, BRFSS và NHANES. Chỉ nhập số liệu giả lập; kết quả không phải chẩn đoán.'
                  : view === 'chat'
                  ? 'Rule Agent kiểm soát an toàn trước khi Knowledge Agent truy xuất tài liệu từ Neo4j và Response Agent trích dẫn nguồn.'
                  : view === 'arch'
                  ? 'Dữ liệu, đồ thị tri thức, RAG, học tăng cường và luật an toàn cùng đi qua Coordinator tới Response Agent.'
                  : view === 'data'
                  ? t('data.lead')
                  : 'Mô hình DQN học chính sách tối ưu hóa lựa chọn chủ đề giáo dục sức khỏe dựa trên nhu cầu giả lập.'}
              </p>
            </div>

            {view === 'arch' ? <Architecture onGoData={goData} /> : view === 'data' ? (
              <DataModels health={health} anchor={dataAnchor} onAnchorDone={() => setDataAnchor(undefined)} onTryModel={k => { reset('risk'); setKind(k); setValues({}); }} onAsk={() => reset('chat')} />
            ) : (
            <div className={`workgrid ${view === 'chat' ? 'chat-workgrid' : ''}`}>
              <section className="panel">
                {view === 'risk' ? (
                  <>
                    <div className="tabs" role="group" aria-label="Chọn bộ dữ liệu">
                      {datasetTabs.map(([k, label]) => (
                        <button key={k} className={kind === k ? 'selected' : ''} aria-pressed={kind === k} onClick={() => switchKind(k)}>
                          {label}
                        </button>
                      ))}
                    </div>
                    <p className="form-notice" role="status">{notice}</p>

                    {(kind === 'nhanes_research' || kind === 'nhanes15_research') && <p className="chat-note">Chỉ nhập số liệu giả lập. Mô hình thử nghiệm phân loại câu trả lời khảo sát NHANES Hoa Kỳ về chẩn đoán trước đó; không dự báo bệnh mới, sàng lọc hay chẩn đoán cho cá nhân. BMI của biểu mẫu 15 chỉ số được tính từ cân nặng và chiều cao.</p>}

                    <form
                      onSubmit={e => {
                        e.preventDefault();
                        if (kind === 'brfss') {
                          const { weight_kg, height_cm, ...features } = values;
                          const weight = Number(weight_kg);
                          const height = Number(height_cm) / 100;
                          const bmi = weight / (height * height);
                          if (!Number.isFinite(bmi) || bmi < 10 || bmi > 100) {
                            setAnswer(null);
                            setError('Cân nặng và chiều cao tương ứng với BMI ngoài khoảng mô hình hỗ trợ (10–100). Vui lòng kiểm tra lại.');
                            return;
                          }
                          run('predict', { kind, features: { ...features, _BMI5: bmi } });
                        } else if (kind === 'nhanes15_research') {
                          const bmi = Number(values.BMXWT) / (Number(values.BMXHT) / 100) ** 2;
                          if (!Number.isFinite(bmi) || bmi < 10 || bmi > 100) {
                            setAnswer(null); setError('BMI tính từ cân nặng và chiều cao cần nằm trong khoảng 10–100.'); return;
                          }
                          run('predict', { kind, features: { ...values, BMXBMI: bmi } });
                        } else {
                          run('predict', { kind, features: values });
                        }
                      }}
                    >
                      <p className="form-intro">Điền số từ phiếu xét nghiệm của bạn hoặc số giả lập. Mọi ô đều bắt buộc.</p>
                      {kind === 'nhanes15_research' ? (
                        <div className="formgroups">
                          {nhanes15Groups.map(g => (
                            <fieldset className="fieldset" key={g.legend}>
                              <legend>{g.legend}</legend>
                              <div className="formgrid">
                                {g.legend === 'Thông tin chung' && (
                                  <label>Giới tính (theo khảo sát NHANES) {select('RIAGENDR', [['1', 'Nam'], ['2', 'Nữ']])}</label>
                                )}
                                {g.fields.map(numberField)}
                              </div>
                            </fieldset>
                          ))}
                        </div>
                      ) : (
                      <div className="formgrid">
                        {kind === 'brfss' ? (
                          <>
                            <label>
                              Cân nặng (kg)
                              <input
                                type="number"
                                step="0.1"
                                min="1"
                                max="500"
                                required
                                placeholder="Ví dụ: 65"
                                value={values.weight_kg || ''}
                                onChange={e => setValues({ ...values, weight_kg: e.target.value })}
                              />
                            </label>
                            <label>
                              Chiều cao (cm)
                              <input
                                type="number"
                                step="0.1"
                                min="1"
                                max="300"
                                required
                                placeholder="Ví dụ: 170"
                                value={values.height_cm || ''}
                                onChange={e => setValues({ ...values, height_cm: e.target.value })}
                              />
                            </label>
                            {Object.entries(brfssOptions).map(([k, o]) => (
                              <label key={k}>
                                {brfssLabels[k].label}
                                <small className="field-hint">{brfssLabels[k].hint}</small>
                                {select(k, o)}
                              </label>
                            ))}
                          </>
                        ) : kind === 'nhanes_research' ? (
                          <>{nhanesBasicFields.map(numberField)}</>
                        ) : (
                          <>
                            <label>
                              Tuổi (1 – 120)
                              <input
                                type="number"
                                min="1"
                                max="120"
                                required
                                placeholder="Ví dụ: 45"
                                value={values.age || ''}
                                onChange={e => setValues({ ...values, age: e.target.value })}
                              />
                            </label>
                            <label>
                              Giới tính sinh học
                              {select('gender', [
                                ['male', 'Nam'],
                                ['female', 'Nữ']
                              ])}
                            </label>
                            {symptoms.map(([k, l, desc]) => (
                              <label key={k}>
                                {l}
                                <small className="field-hint">{desc}</small>
                                {select(k, [
                                  ['yes', 'Có biểu hiện'],
                                  ['no', 'Không']
                                ])}
                              </label>
                            ))}
                          </>
                        )}
                      </div>
                      )}
                      <button disabled={busy} className="primary" type="submit" aria-describedby={error ? 'form-error' : undefined}>
                        {busy ? 'Đang phân tích dữ liệu…' : 'Chạy phân loại mô hình'} <span aria-hidden="true">↗</span>
                      </button>
                    </form>
                  </>
                ) : view === 'chat' ? (
                  <div className="chat-shell">
                    <div className="chat-topbar"><div><strong>Trợ lý Đường An</strong><small>Câu trả lời có nguồn tham khảo</small></div><button type="button" className="chat-clear" disabled={busy || !conversation.length} onClick={() => { setConversation([]); setQuestion(''); setError(''); setChatStatus(''); }}>Cuộc trò chuyện mới</button></div>
                    <div
                      className="chat-messages" role="log" aria-live="polite" aria-busy={busy} aria-label="Nội dung cuộc trò chuyện" tabIndex={0}
                      onScroll={e => { const t = e.currentTarget; nearBottom.current = t.scrollHeight - t.scrollTop - t.clientHeight < 80; }}
                    >
                      {!conversation.length && <div className="chat-welcome"><span className="chat-welcome-icon" aria-hidden="true">✳</span><h2>Hôm nay bạn muốn tìm hiểu điều gì?</h2><p>Đặt câu hỏi về bệnh tiểu đường và tiếp tục trao đổi theo ngữ cảnh.</p><div className="chat-suggestions">{starterQuestions.map(q => <button className="pill" type="button" key={q} onClick={() => { setQuestion(q); document.getElementById('chat-question')?.focus(); }}>{q}</button>)}</div></div>}
                      {conversation.map((turn, index) => {
                        const isLast = index === conversation.length - 1;
                        if (turn.role === 'user') {
                          return <div key={index} className="chat-row user"><div className="chat-bubble"><div className="chat-text">{turn.content}</div></div></div>;
                        }
                        const asked = conversation[index - 1]?.role === 'user' ? conversation[index - 1].content : '';
                        return (
                          <AssistantBubble
                            key={index} turn={turn} index={index}
                            streaming={busy && isLast && !turn.done && !turn.error && !turn.stopped}
                            traceOpen={false}
                            canRetry={isLast && !busy}
                            onRetry={() => sendChat(true)}
                            onAskAgain={() => askAgain(asked)}
                            onGoData={goData}
                            onStatus={setChatStatus}
                          />
                        );
                      })}
                      {waiting && <PendingTurn key={pendingSince} startedAt={pendingSince} onSlow={() => setChatStatus(t('status.slow'))} />}
                      <div ref={chatEnd} />
                    </div>
                    <p className="sr-only" role="status">{chatStatus}</p>
                    <form className="chat-composer" onSubmit={e => { e.preventDefault(); sendChat(); }}>
                      <label className="sr-only" htmlFor="chat-question">Nhập câu hỏi</label>
                      <textarea id="chat-question" required minLength={2} maxLength={1500} rows={2} value={question} onChange={e => setQuestion(e.target.value)} onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing && e.keyCode !== 229) { e.preventDefault(); sendChat(); } }} placeholder="Nhập câu hỏi của bạn…" aria-describedby={ollamaDown ? 'chat-hint chat-hint-off' : 'chat-hint'} />
                      {busy
                        ? <button type="button" className="chat-stop" aria-label="Dừng câu trả lời" onClick={stopChat}>Dừng</button>
                        : <button type="submit" disabled={ollamaDown || question.trim().length < 2} aria-label="Gửi câu hỏi">↑</button>}
                    </form>
                    {question.length >= 1300 && <small className="chat-counter" aria-live="off">{question.length}/1500 ký tự</small>}
                    {ollamaDown && <p className="chat-note chat-note-warn" id="chat-hint-off">{MSG_OLLAMA_DOWN}</p>}
                    <p className="chat-note" id="chat-hint">Enter để gửi, Shift+Enter xuống dòng. Hội thoại chỉ lưu trong phiên này. Không nhập thông tin cá nhân hoặc bệnh án thật. Nội dung chỉ để tham khảo.</p>
                  </div>
                ) : (
                  <>
                    <div className="rl-header">
                      <h3>Trạng thái nhu cầu học tập giả lập</h3>
                      <p>Đánh dấu các chủ đề mà người học giả lập CHƯA nắm vững:</p>
                    </div>
                    {[
                      'Tổng quan về bệnh đái tháo đường',
                      'Ăn uống cân bằng và kiểm soát carbohydrate',
                      'Vận động thể chất và luyện tập thể thao',
                      'Theo dõi đường huyết và tự chăm sóc'
                    ].map((topic, i) => (
                      <label className="check" key={topic}>
                        <input
                          type="checkbox"
                          checked={Boolean(needs[i])}
                          onChange={e =>
                            setNeeds(needs.map((v, j) => (j === i ? Number(e.target.checked) : v)))
                          }
                        />
                        <span>{topic}</span>
                      </label>
                    ))}
                    <button
                      className="primary"
                      disabled={busy}
                      onClick={() => run('learning', { needs })}
                    >
                      {busy ? 'Đang suy luận chính sách…' : 'Chạy đề xuất DQN'} <span aria-hidden="true">↗</span>
                    </button>
                    <p className="rl-explain">DQN là mô hình học tăng cường: nó chọn chủ đề giúp người học giả lập tiến bộ nhiều nhất.</p>
                  </>
                )}
                {error && (
                  <div className="error" id="form-error" role="alert" tabIndex={-1} ref={errorRef}>
                    {error}
                  </div>
                )}
              </section>

              {view !== 'chat' && <aside className="result">
                <p className="sr-only" role="status">{resultStatus}</p>
                <div className="eyebrow">KẾT QUẢ ĐIỀU PHỐI</div>
                {answer ? (
                  <>
                    <h2 tabIndex={-1} ref={resultHead}>
                      {completed
                        ? 'Tất cả các chủ đề đã hoàn thành'
                        : answer.topic
                        ? (view === 'rl' ? `Chủ đề nên học tiếp: ${answer.topic}` : answer.topic)
                        : answer.score !== undefined
                        ? 'Điểm phân loại của mô hình'
                        : 'Thông tin tri thức'}
                    </h2>

                    {answer.policy_overridden && <p className="rl-note">Luật an toàn đã điều chỉnh đề xuất của mô hình DQN.</p>}

                    {answer.score !== undefined && (
                      <div className="score-card">
                        <p className="score-banner">Kết quả thử nghiệm trên dữ liệu khảo sát, không phải chẩn đoán.</p>
                        <div className="score-label">Điểm của mô hình (0 đến 1)</div>
                        <div className="score">
                          {answer.score.toLocaleString('vi-VN', { minimumFractionDigits: 3, maximumFractionDigits: 3 })}
                        </div>
                        <div className="classification-badge">
                          {answer.classification
                            ? `Mô hình xếp vào nhóm giống người từng được chẩn đoán đái tháo đường (ngưỡng ${thresholdText})`
                            : `Mô hình xếp vào nhóm ít giống người từng được chẩn đoán đái tháo đường (ngưỡng ${thresholdText})`}
                        </div>
                        <p className="meaning-text">{answer.meaning}</p>
                        <p className="score-note">Điểm này không phải xác suất bạn mắc bệnh. Hãy hỏi bác sĩ nếu bạn lo lắng.</p>
                        <p className="score-note model-info">{t('risk.modelInfo')} <button type="button" className="linkbutton" onClick={() => goData(`model-${kind}`)}>{t('risk.modelInfo.link')} →</button></p>
                      </div>
                    )}

                    {answer.message && <p className="success-banner">{answer.message}</p>}

                    {answer.answer && <div className="response">{answer.answer}</div>}

                    {answer.sources && answer.sources.length > 0 && <SourceList sources={answer.sources} />}

                    {answer.trace && answer.trace.length > 0 && <TracePipeline trace={answer.trace} />}

                    <div className="disclaimer-box">
                      <small>{view === 'rl' ? RL_DISCLAIMER : answer.disclaimer || 'Chỉ nhằm mục đích học tập, không phải chẩn đoán hay tư vấn y tế.'}</small>
                    </div>
                  </>
                ) : (
                  <div className="empty-state">
                    <div className="emptyicon" aria-hidden="true">✳</div>
                    <h2>Sẵn sàng hỗ trợ bạn.</h2>
                    <p>Hãy hoàn tất biểu mẫu hoặc gửi câu hỏi để quan sát hệ đa Agent phối hợp xử lý.</p>
                  </div>
                )}
              </aside>}
            </div>
            )}
          </>
        )}
      </main>

      <footer>
        <div>
          <strong><span aria-hidden="true">✳</span> đường an</strong> — Hệ đa tác tử học thuật nghiên cứu bệnh đái tháo đường.
        </div>
        <div>Kiến thức tham khảo cho mục đích học tập</div>
        <span>PHI LÂM SÀNG · DỰ ÁN HỌC THUẬT</span>
      </footer>
    </div>
  );
}

createRoot(document.getElementById('root')!).render(<App />);
