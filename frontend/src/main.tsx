import React, { useState, useEffect, useRef } from 'react';
import { createRoot } from 'react-dom/client';
import './style.css';

type Answer = {
  answer?: string;
  sources?: { title: string; url: string; topic?: string; review_status?: string | null; fetched_at?: string | null }[];
  trace?: string[];
  score?: number;
  classification?: number;
  threshold?: number;
  topic?: string;
  disclaimer?: string;
  meaning?: string;
  model?: string;
  status?: string;
  message?: string;
};

type ChatTurn = {
  role: 'user' | 'assistant';
  content: string;
  sources?: Answer['sources'];
  trace?: string[];
  isError?: boolean;
};

type HealthStatus = {
  status: string;
  models: { symptoms: boolean; brfss: boolean; nhanes_research: boolean; nhanes15_research: boolean };
  rl: boolean;
  services?: { neo4j: boolean; ollama: boolean };
};

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
  ['rl', 'Mô phỏng RL']
] as const;

const starterQuestions = [
  'Những triệu chứng cảnh báo điển hình của đái tháo đường là gì?',
  'Người bệnh đái tháo đường cần lưu ý điều gì khi chăm sóc bàn chân?',
  'Khuyến nghị về thời gian vận động thể lực mỗi tuần là bao nhiêu?',
  'Phương pháp đĩa ăn đái tháo đường của ADA phân chia ra sao?'
];

async function postApi(path: string, body: unknown): Promise<Answer> {
  const r = await fetch('/api/' + path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  const data = await r.json();
  if (!r.ok) {
    throw Error(typeof data.detail === 'string' ? data.detail : 'Không thể xử lý yêu cầu.');
  }
  return data;
}

function App() {
  const [view, setView] = useState<'home' | 'risk' | 'chat' | 'rl'>('home');
  const [kind, setKind] = useState<'symptoms' | 'brfss' | 'nhanes_research' | 'nhanes15_research'>('nhanes15_research');
  const [values, setValues] = useState<Record<string, string>>({});
  const [answer, setAnswer] = useState<Answer | null>(null);
  const [question, setQuestion] = useState('');
  const [conversation, setConversation] = useState<ChatTurn[]>([]);
  const chatEnd = useRef<HTMLDivElement>(null);
  const [needs, setNeeds] = useState<number[]>([1, 1, 1, 1]);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const servicesReady = health?.status === 'ok' && health.services?.neo4j === true && health.services?.ollama === true;

  useEffect(() => {
    fetch('/api/health')
      .then(res => res.json())
      .then(data => setHealth(data))
      .catch(() => setHealth(null));
  }, []);

  useEffect(() => {
    if (view === 'chat') chatEnd.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }, [conversation, busy, view]);

  const reset = (v: 'home' | 'risk' | 'chat' | 'rl') => {
    setView(v);
    setAnswer(null);
    setError('');
  };

  async function run(path: string, body: unknown) {
    setBusy(true);
    setError('');
    setAnswer(null);
    try {
      const res = await postApi(path, body);
      setAnswer(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Có lỗi xảy ra.');
    } finally {
      setBusy(false);
    }
  }

  async function sendChat() {
    const text = question.trim();
    if (busy || text.length < 2) {
      if (text.length < 2) setError('Vui lòng nhập câu hỏi có ít nhất 2 ký tự.');
      return;
    }
    const history = conversation.filter(turn => !turn.isError).slice(-10)
      .map(turn => ({ role: turn.role, content: turn.content.slice(0, 1500) }));
    setConversation(current => [...current, { role: 'user', content: text }]);
    setQuestion('');
    setError('');
    setBusy(true);
    try {
      const response = await fetch('/api/chat/stream', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: text, history })
      });
      if (!response.ok || !response.body) throw Error('Không thể kết nối tới dịch vụ hỏi đáp.');
      setConversation(current => [...current, { role: 'assistant', content: '' }]);
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let done = false;
      const updateLast = (change: Partial<ChatTurn>) => setConversation(current => {
        const copy = [...current];
        const last = copy[copy.length - 1];
        if (last?.role === 'assistant') copy[copy.length - 1] = { ...last, ...change, content: change.content === undefined ? last.content : last.content + change.content };
        return copy;
      });
      while (true) {
        const chunk = await reader.read();
        buffer += decoder.decode(chunk.value, { stream: !chunk.done });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        for (const line of lines) {
          if (!line) continue;
          const event = JSON.parse(line);
          if (event.type === 'delta') updateLast({ content: event.text });
          if (event.type === 'done') { updateLast({ sources: event.sources, trace: event.trace }); done = true; }
          if (event.type === 'error') throw Error(event.message);
        }
        if (chunk.done) break;
      }
      if (!done) throw Error('Kết nối bị gián đoạn. Vui lòng thử lại.');
    } catch (e) {
      const message = e instanceof Error ? e.message : 'Có lỗi xảy ra.';
      setConversation(current => {
        const last = current[current.length - 1];
        if (last?.role === 'assistant') return [...current.slice(0, -1), { ...last, content: last.content ? last.content + '\n\n' + message : message, isError: true }];
        return [...current, { role: 'assistant', content: message, isError: true }];
      });
      setQuestion(text);
    } finally {
      setBusy(false);
    }
  }

  const select = (name: string, choices: [string, string][]) => (
    <select
      required
      value={values[name] || ''}
      onChange={e => setValues({ ...values, [name]: e.target.value })}
    >
      <option value="">-- Chọn câu trả lời --</option>
      {choices.map(([v, l]) => (
        <option key={v} value={v}>
          {l}
        </option>
      ))}
    </select>
  );

  return (
    <div className="shell">
      <header>
        <button className="brand" onClick={() => reset('home')}>
          <span className="logo">✳</span>
          <span>
            đường an<small>THÔNG TIN VỀ ĐÁI THÁO ĐƯỜNG</small>
          </span>
        </button>
        <nav>
          {views.map(([v, l]) => (
            <button
              key={v}
              className={view === v ? 'active' : ''}
              onClick={() => reset(v)}
            >
              {l}
            </button>
          ))}
        </nav>
        <div className="header-status">
          <span className={`status-dot ${servicesReady ? 'online' : 'offline'}`} />
          <span className="status-text">
            {servicesReady ? 'Dịch vụ: Trực tuyến' : health ? 'Một số dịch vụ chưa sẵn sàng' : 'Không kết nối được API'}
          </span>
        </div>
      </header>

      <main>
        {view === 'home' ? (
          <>
            <section className="hero">
              <div>
                <div className="eyebrow">
                  <span /> KIẾN THỨC Y TẾ DỰA TRÊN DỮ LIỆU & NGUỒN CHÍNH THỨC
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
                  <span>✳</span>
                </div>
                <div className="art-card">
                  <div className="pulse">✦</div>
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
                Hệ thống gồm Prediction Agent, Knowledge Agent, Rule Agent, Learning Agent và Response Agent được điều phối bởi Coordinator.
              </p>
            </section>

            <section className="cards">
              {[
                ['01', 'Đánh giá mô hình', 'Thử nghiệm phân loại trên dữ liệu UCI, BRFSS và NHANES.', 'risk'],
                ['02', 'Hỏi đáp có nguồn', 'Đặt câu hỏi và xem các nguồn tham khảo đi kèm.', 'chat'],
                ['03', 'Mô phỏng RL', 'Tác tử học tăng cường DQN tự động đề xuất lộ trình chủ đề giáo dục phù hợp.', 'rl']
              ].map(([n, t, d, v]) => (
                <button className="feature" key={n} onClick={() => reset(v as any)}>
                  <span className="feature-no">
                    {n} <i>↗</i>
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
                ĐƯỜNG AN / {view === 'risk' ? 'ĐÁNH GIÁ MÔ HÌNH' : view === 'chat' ? 'HỎI ĐÁP ĐA AGENT' : 'MÔ PHỎNG RL'}
              </div>
              <h1>
                {view === 'risk'
                  ? 'Khám phá dữ liệu và mô hình phân loại'
                  : view === 'chat'
                  ? 'Hỏi đáp thông tin y tế có nguồn'
                  : 'Học tăng cường điều phối lộ trình học tập'}
              </h1>
              <p>
                {view === 'risk'
                  ? 'Các thí nghiệm phân loại trên dữ liệu UCI, BRFSS và NHANES. Chỉ nhập số liệu giả lập; kết quả không phải chẩn đoán.'
                  : view === 'chat'
                  ? 'Rule Agent kiểm soát an toàn trước khi Knowledge Agent truy xuất tài liệu từ Neo4j và Response Agent trích dẫn nguồn.'
                  : 'Mô hình DQN học chính sách tối ưu hóa lựa chọn chủ đề giáo dục sức khỏe dựa trên nhu cầu giả lập.'}
              </p>
            </div>

            <div className={`workgrid ${view === 'chat' ? 'chat-workgrid' : ''}`}>
              <section className="panel">
                {view === 'risk' ? (
                  <>
                    <div className="tabs">
                      <button className={kind === 'nhanes15_research' ? 'selected' : ''} onClick={() => { setKind('nhanes15_research'); setValues({}); setAnswer(null); }}>
                        NHANES 15 chỉ số
                      </button>
                      <button className={kind === 'nhanes_research' ? 'selected' : ''} onClick={() => { setKind('nhanes_research'); setValues({}); setAnswer(null); }}>
                        Chỉ số xét nghiệm (NHANES thử nghiệm)
                      </button>
                      <button
                        className={kind === 'brfss' ? 'selected' : ''}
                        onClick={() => {
                          setKind('brfss');
                          setValues({});
                          setAnswer(null);
                        }}
                      >
                        Khảo sát Sức khỏe & Lối sống (BRFSS)
                      </button>
                      <button
                        className={kind === 'symptoms' ? 'selected' : ''}
                        onClick={() => {
                          setKind('symptoms');
                          setValues({});
                          setAnswer(null);
                        }}
                      >
                        Triệu chứng lâm sàng sớm (UCI)
                      </button>
                    </div>

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
                        ) : kind === 'nhanes15_research' ? (
                          <>
                            <label>Giới tính theo mã khảo sát NHANES {select('RIAGENDR', [['1', 'Nam'], ['2', 'Nữ']])}</label>
                            {([
                              ['RIDAGEYR', 'Tuổi (năm)', 18, 80, '1'],
                              ['BMXWT', 'Cân nặng (kg)', 20, 350, '0.1'],
                              ['BMXHT', 'Chiều cao (cm)', 100, 250, '0.1'],
                              ['BMXWAIST', 'Vòng eo (cm)', 30, 250, '0.1'],
                              ['BPXSY1', 'Huyết áp tâm thu (mmHg)', 50, 300, '1'],
                              ['BPXDI1', 'Huyết áp tâm trương (mmHg)', 20, 200, '1'],
                              ['LBXGLU', 'Glucose huyết tương lúc đói (mg/dL)', 40, 500, '0.1'],
                              ['LBXGH', 'HbA1c (%)', 3, 20, '0.1'],
                              ['LBXTC', 'Cholesterol toàn phần (mg/dL)', 50, 800, '0.1'],
                              ['LBDHDD', 'HDL cholesterol (mg/dL)', 5, 200, '0.1'],
                              ['LBXTR', 'Triglyceride (mg/dL)', 10, 3000, '0.1'],
                              ['LBXSATSI', 'ALT (U/L)', 1, 1000, '0.1'],
                              ['LBXSCR', 'Creatinine huyết thanh (mg/dL)', 0.1, 15, '0.01']
                            ] as const).map(([key, label, min, max, step]) => (
                              <label key={key}>{label}<input type="number" min={min} max={max} step={step} required value={values[key] || ''} onChange={e => setValues({ ...values, [key]: e.target.value })} /></label>
                            ))}
                          </>
                        ) : kind === 'nhanes_research' ? (
                          <>
                            {([
                              ['RIDAGEYR', 'Tuổi (năm)', 18, 80, '1'],
                              ['BMXBMI', 'BMI (kg/m²)', 10, 100, '0.1'],
                              ['LBXGLU', 'Glucose huyết tương lúc đói (mg/dL)', 40, 500, '0.1'],
                              ['LBXGH', 'HbA1c (%)', 3, 20, '0.1']
                            ] as const).map(([key, label, min, max, step]) => (
                              <label key={key}>{label}
                                <input type="number" min={min} max={max} step={step} required value={values[key] || ''} onChange={e => setValues({ ...values, [key]: e.target.value })} />
                              </label>
                            ))}
                          </>
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
                      <button disabled={busy} className="primary" type="submit">
                        {busy ? 'Đang phân tích dữ liệu…' : 'Chạy phân loại mô hình'} <span>↗</span>
                      </button>
                    </form>
                  </>
                ) : view === 'chat' ? (
                  <div className="chat-shell">
                    <div className="chat-topbar"><div><strong>Trợ lý Đường An</strong><small>Câu trả lời có nguồn tham khảo</small></div><button type="button" className="chat-clear" disabled={busy || !conversation.length} onClick={() => { setConversation([]); setQuestion(''); setError(''); }}>Cuộc trò chuyện mới</button></div>
                    <div className="chat-messages" aria-live="polite" aria-label="Nội dung cuộc trò chuyện">
                      {!conversation.length && <div className="chat-welcome"><span className="chat-welcome-icon">✳</span><h2>Hôm nay bạn muốn tìm hiểu điều gì?</h2><p>Đặt câu hỏi về bệnh tiểu đường và tiếp tục trao đổi theo ngữ cảnh.</p><div className="chat-suggestions">{starterQuestions.map(q => <button className="pill" type="button" key={q} onClick={() => setQuestion(q)}>{q}</button>)}</div></div>}
                      {conversation.map((turn, index) => <div key={index} className={`chat-row ${turn.role}`}>
                        {turn.role === 'assistant' && <span className="chat-avatar">✳</span>}
                        <div className={`chat-bubble ${turn.isError ? 'chat-error' : ''}`}><div className="chat-text">{turn.content}</div>
                          {!!turn.sources?.length && <div className="chat-sources"><strong>Nguồn tham khảo</strong>{turn.sources.map((source, i) => <a key={i} href={source.url} target="_blank" rel="noreferrer">[{i + 1}] {source.title} ↗{source.review_status === 'unreviewed_web' && <small> Tự động thu thập, chưa kiểm duyệt chuyên môn</small>}</a>)}</div>}
                          {!!turn.trace?.length && <details className="chat-trace"><summary>Quá trình xử lý</summary><span>{turn.trace.join(' → ')}</span></details>}
                        </div>
                      </div>)}
                      {busy && conversation[conversation.length - 1]?.role !== 'assistant' && <div className="chat-row assistant"><span className="chat-avatar">✳</span><div className="chat-bubble chat-thinking">Đang tìm trong kho tri thức…</div></div>}
                      <div ref={chatEnd} />
                    </div>
                    <form className="chat-composer" onSubmit={e => { e.preventDefault(); sendChat(); }}>
                      <label className="sr-only" htmlFor="chat-question">Nhập câu hỏi</label>
                      <textarea id="chat-question" required minLength={2} maxLength={1500} rows={2} value={question} onChange={e => setQuestion(e.target.value)} onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); sendChat(); } }} placeholder="Nhập câu hỏi của bạn…" />
                      <button type="submit" disabled={busy || question.trim().length < 3} aria-label="Gửi câu hỏi">↑</button>
                    </form>
                    <p className="chat-note">Hội thoại chỉ lưu trong phiên này. Không nhập thông tin cá nhân hoặc bệnh án thật. Nội dung chỉ để tham khảo.</p>
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
                      {busy ? 'Đang suy luận chính sách…' : 'Chạy đề xuất DQN'} <span>↗</span>
                    </button>
                  </>
                )}
                {error && (
                  <div className="error" role="alert">
                    {error}
                  </div>
                )}
              </section>

              {view !== 'chat' && <aside className="result">
                <div className="eyebrow">KẾT QUẢ ĐIỀU PHỐI</div>
                {answer ? (
                  <>
                    <h2>
                      {answer.topic ||
                        (answer.score !== undefined
                          ? 'Điểm phân loại của mô hình'
                          : 'Thông tin tri thức')}
                    </h2>

                    {answer.score !== undefined && (
                      <div className="score-card">
                        <div className="score">
                          {answer.score.toFixed(3)}
                          <small> / 1</small>
                        </div>
                        <div className="classification-badge">
                          Lớp dự đoán tại ngưỡng {answer.threshold ?? 0.5}:{' '}
                          <strong>
                            {answer.classification ? 'Lớp 1' : 'Lớp 0'}
                          </strong>
                        </div>
                        <p className="meaning-text">{answer.meaning}</p>
                      </div>
                    )}

                    {answer.message && <p className="success-banner">{answer.message}</p>}

                    {answer.answer && <div className="response">{answer.answer}</div>}

                    {answer.sources && answer.sources.length > 0 && (
                      <div className="sources-container">
                        <h3>Nguồn tham khảo</h3>
                        {answer.sources.map((s, idx) => (
                          <a
                            className="source-card"
                            key={idx}
                            href={s.url}
                            target="_blank"
                            rel="noreferrer"
                          >
                            <span className="source-index">[{idx + 1}]</span>
                            <div>
                              <strong>{s.title}</strong>
                              <small>{s.url}</small>
                              {s.review_status === 'unreviewed_web' && <small>Nội dung tự động thu thập, chưa được kiểm duyệt chuyên môn{s.fetched_at ? ` · ${new Date(s.fetched_at).toLocaleDateString('vi-VN')}` : ''}</small>}
                            </div>
                            <span className="source-arrow">↗</span>
                          </a>
                        ))}
                      </div>
                    )}

                    {answer.trace && (
                      <div className="trace-box">
                        <div className="trace-title">Tiến trình thực thi của hệ đa Agent (Execution Trace):</div>
                        <div className="trace-steps">
                          {answer.trace.map((step, idx) => (
                            <span key={idx} className="trace-badge">
                              {step}
                              {idx < answer.trace!.length - 1 && <span className="trace-arrow"> → </span>}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="disclaimer-box">
                      <small>{answer.disclaimer}</small>
                    </div>
                  </>
                ) : (
                  <div className="empty-state">
                    <div className="emptyicon">✳</div>
                    <h2>Sẵn sàng hỗ trợ bạn.</h2>
                    <p>Hãy hoàn tất biểu mẫu hoặc gửi câu hỏi để quan sát hệ đa Agent phối hợp xử lý.</p>
                  </div>
                )}
              </aside>}
            </div>
          </>
        )}
      </main>

      <footer>
        <div>
          <strong>✳ đường an</strong> — Hệ đa tác tử học thuật nghiên cứu bệnh đái tháo đường.
        </div>
        <div>Kiến thức tham khảo cho mục đích học tập</div>
        <span>PHI LÂM SÀNG · DỰ ÁN HỌC THUẬT</span>
      </footer>
    </div>
  );
}

createRoot(document.getElementById('root')!).render(<App />);
