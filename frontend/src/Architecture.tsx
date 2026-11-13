import React from 'react';
import { t } from './copy.ts';

type BoxProps = { title: string; desc: string; cls?: string; reads?: string; extra?: string };

function Box({ title, desc, cls = '', reads, extra }: BoxProps) {
  return (
    <div className={`arch-box ${cls}`}>
      <strong>{title}</strong>
      <small>{desc}</small>
      {extra && <small>{extra}</small>}
      {reads && <small className="arch-reads">Đọc từ: {reads}</small>}
    </div>
  );
}

const Link = ({ label }: { label: string }) => (
  <div className="arch-link" aria-hidden="true"><span>{label}</span></div>
);

const legend: [string, string][] = [
  ['rule', 'Rule Agent'], ['know', 'Knowledge Agent'], ['graph', 'Knowledge Graph Agent'], ['pred', 'Prediction Agent'],
  ['learn', 'Learning Agent'], ['conv', 'Conversation Agent'], ['coord', 'Coordinator'], ['resp', 'Response Agent']
];

const flow = [
  'Coordinator nhận câu hỏi và chuyển cho Rule Agent.',
  'Rule Agent kiểm tra an toàn. Nếu nguy hiểm thì dừng và đưa cảnh báo.',
  'Knowledge Agent tìm tài liệu gần nghĩa.',
  'Knowledge Graph Agent tra thêm quan hệ và tài liệu gốc trong Neo4j.',
  'Response Agent viết câu trả lời có trích dẫn, kèm nguồn và các bước đã chạy.'
];

export function Architecture({ onGoData }: { onGoData?: (anchor?: string) => void }) {
  return (
    <div className="panel arch">
      <section aria-labelledby="arch-l1" className="arch-layer">
        <h2 id="arch-l1">Dữ liệu và tri thức</h2>
        <div className="arch-row">
          <Box title="Dữ liệu có sẵn" desc="UCI · BRFSS · NHANES" />
          <Link label="huấn luyện" />
          <Box title="Deep Learning (CNN 1D / MLP)" desc="Mô hình dự đoán / phân loại học từ dữ liệu có sẵn" cls="pred" />
        </div>
        <div className="arch-row">
          <Box title="Web, sách, hướng dẫn" desc="WHO · ADA · CDC · NIDDK · Bộ Y tế" />
          <Link label="tạo" />
          <Box title="Neo4j KB" desc={t('arch.kb.desc')} cls="graph" />
        </div>
      </section>
      <div className="arch-down" aria-hidden="true">↓</div>
      <section aria-labelledby="arch-l2" className="arch-layer">
        <h2 id="arch-l2">Các tác tử</h2>
        <div className="arch-grid">
          <Box title="Prediction Agent" desc="Học sâu (CNN 1D, MLP) dự đoán / phân loại từ chỉ số" cls="pred" reads="Dữ liệu có sẵn" />
          <Box title="Knowledge Agent" desc="Tìm đoạn tài liệu gần nghĩa (RAG)" cls="know" reads="Neo4j KB" />
          <Box title="Knowledge Graph Agent" desc="Tra quan hệ, ngưỡng, tài liệu gốc trong đồ thị" cls="graph" reads="Neo4j KB" />
          <Box title="Rule Agent" desc="Chặn cấp cứu, hỏi liều thuốc, lộ thông tin cá nhân, prompt injection trước khi tra cứu" extra="Rule duyệt xong mới tới Knowledge Agent." cls="rule" />
          <Box title="Learning Agent" desc="Học tăng cường (DQN) + luật bảo vệ, chọn chủ đề nên học tiếp" cls="learn" />
          <Box title="Conversation Agent" desc="Trả lời lời chào, giữ ngữ cảnh" cls="conv" />
        </div>
      </section>
      <div className="arch-down" aria-hidden="true">↓</div>
      <section aria-labelledby="arch-l3" className="arch-layer">
        <h2 id="arch-l3">Điều phối và phản hồi</h2>
        <div className="arch-grid">
          <Box title="Coordinator (LangGraph)" desc="Định tuyến theo trạng thái" cls="coord" />
          <Box title="Response Agent (LLM)" desc="Viết câu trả lời chỉ từ nguồn, có trích dẫn [n]" cls="resp" />
          <Box title="Tư vấn / trợ giúp" desc="Đầu ra cho người dùng, kèm cảnh báo phi lâm sàng" />
        </div>
      </section>
      <section aria-labelledby="arch-flow" className="arch-layer">
        <h2 id="arch-flow">Một câu hỏi đi qua đâu</h2>
        <ol className="arch-steps">{flow.map(t => <li key={t}>{t}</li>)}</ol>
      </section>
      <div className="arch-legend">
        <p className="chat-note">Màu viền trái của từng tác tử giống màu thẻ trong "Luồng xử lý" ở tab Hỏi đáp.</p>
        <ul>{legend.map(([c, n]) => <li key={c}><span className={`arch-swatch arch-box ${c}`} aria-hidden="true" />{n}</li>)}</ul>
      </div>
      {onGoData && <p className="arch-todata"><button type="button" className="linkbutton" onClick={() => onGoData()}>{t('arch.toData')}</button></p>}
    </div>
  );
}
