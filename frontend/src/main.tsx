import React, { useState, useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import './style.css';

type Answer = {
  answer?: string;
  sources?: { title: string; url: string; topic?: string }[];
  trace?: string[];
  score?: number;
  classification?: number;
  topic?: string;
  disclaimer?: string;
  meaning?: string;
  model?: string;
  status?: string;
  message?: string;
};

type HealthStatus = {
  status: string;
  models: { symptoms: boolean; brfss: boolean };
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
  ['chat', 'Hỏi đáp đa Agent'],
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
  const [kind, setKind] = useState<'symptoms' | 'brfss'>('brfss');
  const [values, setValues] = useState<Record<string, string>>({});
  const [answer, setAnswer] = useState<Answer | null>(null);
  const [question, setQuestion] = useState('');
  const [needs, setNeeds] = useState<number[]>([1, 1, 1, 1]);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [health, setHealth] = useState<HealthStatus | null>(null);

  useEffect(() => {
    fetch('/api/health')
      .then(res => res.json())
      .then(data => setHealth(data))
      .catch(() => setHealth(null));
  }, []);

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
            đường an<small>HỆ ĐA AGENT HỌC THUẬT TIỂU ĐƯỜNG</small>
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
          <span className={`status-dot ${health?.status === 'ok' ? 'online' : 'offline'}`} />
          <span className="status-text">
            {health?.status === 'ok' ? 'Dịch vụ: Trực tuyến' : 'Dịch vụ: Ngoại tuyến'}
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
                  Nền tảng học thuật ứng dụng hệ đa Agent (Multi-Agent System) phối hợp điều phối các mô hình Deep Learning, kho tri thức đồ thị Neo4j, kỹ thuật RAG và Học tăng cường (RL) hỗ trợ tìm hiểu thông tin về bệnh đái tháo đường.
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
                    <strong>Kiến thức có nguồn kiểm chứng.</strong>
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
                ['01', 'Đánh giá mô hình', 'Phân loại dữ liệu dựa trên mô hình mạng nơ-ron PyTorch MLP và Logistic Regression.', 'risk'],
                ['02', 'Hỏi đáp có nguồn', 'Hệ RAG truy xuất tài liệu từ Neo4j và tổng hợp câu trả lời với trích dẫn minh bạch.', 'chat'],
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
                  ? 'Hỏi đáp thông tin y tế có kiểm chứng'
                  : 'Học tăng cường điều phối lộ trình học tập'}
              </h1>
              <p>
                {view === 'risk'
                  ? 'Hai mô hình phân loại: Bộ dữ liệu khảo sát BRFSS (CDC Hoa Kỳ 2021-2023) và Bộ triệu chứng UCI Early Stage (CC BY 4.0).'
                  : view === 'chat'
                  ? 'Rule Agent kiểm soát an toàn trước khi Knowledge Agent truy xuất tài liệu từ Neo4j và Response Agent trích dẫn nguồn.'
                  : 'Mô hình DQN học chính sách tối ưu hóa lựa chọn chủ đề giáo dục sức khỏe dựa trên nhu cầu giả lập.'}
              </p>
            </div>

            <div className="workgrid">
              <section className="panel">
                {view === 'risk' ? (
                  <>
                    <div className="tabs">
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

                    <form
                      onSubmit={e => {
                        e.preventDefault();
                        run('predict', { kind, features: values });
                      }}
                    >
                      <div className="formgrid">
                        {kind === 'brfss' ? (
                          <>
                            <label>
                              Chỉ số BMI (10 – 100)
                              <small className="field-hint">BMI = Cân nặng (kg) / [Chiều cao (m)]²</small>
                              <input
                                type="number"
                                step="0.1"
                                min="10"
                                max="100"
                                required
                                placeholder="Ví dụ: 24.5"
                                value={values._BMI5 || ''}
                                onChange={e => setValues({ ...values, _BMI5: e.target.value })}
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
                  <>
                    <div className="starter-box">
                      <div className="field-hint" style={{ marginBottom: 8, fontWeight: 600 }}>
                        Gợi ý câu hỏi tìm hiểu nhanh:
                      </div>
                      <div className="pills">
                        {starterQuestions.map((q, i) => (
                          <button
                            key={i}
                            type="button"
                            className="pill"
                            onClick={() => setQuestion(q)}
                          >
                            {q}
                          </button>
                        ))}
                      </div>
                    </div>
                    <form
                      onSubmit={e => {
                        e.preventDefault();
                        run('chat', { question });
                      }}
                    >
                      <label>
                        Câu hỏi về bệnh đái tháo đường
                        <textarea
                          required
                          minLength={3}
                          maxLength={1500}
                          value={question}
                          onChange={e => setQuestion(e.target.value)}
                          placeholder="Ví dụ: Những triệu chứng cảnh báo điển hình của bệnh đái tháo đường là gì?"
                        />
                      </label>
                      <p className="hint">
                        🔒 Bảo mật dữ liệu: Tuyệt đối không nhập họ tên cá nhân, số điện thoại, CCCD/CMND hoặc số bệnh án thật.
                      </p>
                      <button className="primary" disabled={busy} type="submit">
                        {busy ? 'Đang truy xuất và tổng hợp…' : 'Gửi câu hỏi tới hệ Agent'} <span>↗</span>
                      </button>
                    </form>
                  </>
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

              <aside className="result">
                <div className="eyebrow">KẾT QUẢ ĐIỀU PHỐI</div>
                {answer ? (
                  <>
                    <h2>
                      {answer.topic ||
                        (answer.score !== undefined
                          ? `Kết quả đánh giá: ${(answer.score * 100).toFixed(1)}%`
                          : 'Thông tin tri thức')}
                    </h2>

                    {answer.score !== undefined && (
                      <div className="score-card">
                        <div className="score">
                          {(answer.score * 100).toFixed(1)}
                          <small> / 100</small>
                        </div>
                        <div
                          className={`classification-badge ${
                            answer.classification ? 'high-risk' : 'low-risk'
                          }`}
                        >
                          Phân loại tại ngưỡng 0.5:{' '}
                          <strong>
                            {answer.classification ? 'Nhóm nguy cơ cao (Dương tính)' : 'Nhóm nguy cơ thấp (Âm tính)'}
                          </strong>
                        </div>
                        <p className="meaning-text">{answer.meaning}</p>
                      </div>
                    )}

                    {answer.message && <p className="success-banner">{answer.message}</p>}

                    {answer.answer && <div className="response">{answer.answer}</div>}

                    {answer.sources && answer.sources.length > 0 && (
                      <div className="sources-container">
                        <h3>Nguồn tài liệu kiểm chứng</h3>
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
              </aside>
            </div>
          </>
        )}
      </main>

      <footer>
        <div>
          <strong>✳ đường an</strong> — Hệ đa tác tử học thuật nghiên cứu bệnh đái tháo đường.
        </div>
        <div>MacBook Pro Apple Silicon M1 Pro · LangGraph · PyTorch · Neo4j · Ollama</div>
        <span>PHI LÂM SÀNG · DỰ ÁN HỌC THUẬT</span>
      </footer>
    </div>
  );
}

createRoot(document.getElementById('root')!).render(<App />);
