/**
 * FIXTURE cho SCR-2 khi `/api/about` chưa có (design 8-Q2). Chỉ dùng ở chế độ dev (`?about=fixture…`),
 * không bao giờ được dùng trong bản build. Số lấy từ wireframe design-ui.md 2d / 6c (report.json 13/11/2026);
 * dữ liệu thật luôn đọc từ API.
 */
import type { AboutInfo } from './about.ts';

export const ABOUT_FIXTURE: AboutInfo = {
  generated_at: '2026-11-13T14:05:00+07:00',
  models: [
    {
      kind: 'nhanes15_research', name: 'NHANES đầy đủ (15 chỉ số)', architecture: 'CNN 1D', available: true,
      dataset: { name: 'NHANES Hoa Kỳ', cycles: ['2015–2016', '2017–2018'], label: 'Tự khai đã từng được chẩn đoán (DIQ010)',
        n_train: 1680, n_validation: 414, n_test: 2038, positive_rate_test: 0.164 },
      threshold: 0.8,
      metrics_test: { roc_auc: 0.931, f1_pos: 0.755, recall_pos: 0.751, precision_pos: 0.758, accuracy: 0.92,
        brier: 0.092, confusion_matrix: [[1624, 80], [83, 251]], auc_ci95: [0.913, 0.949] },
      baseline: { name: 'Hồi quy logistic', split: 'validation', roc_auc: 0.95, f1_pos: 0.67 },
      selection_rule: 'Chọn theo ROC-AUC trên tập validation',
      limitations: ['Nhãn là tự khai, không phải xét nghiệm xác nhận.']
    },
    {
      kind: 'nhanes_research', name: 'NHANES rút gọn (4 chỉ số)', architecture: 'CNN 1D', available: true,
      dataset: { name: 'NHANES Hoa Kỳ', label: 'Tự khai đã từng được chẩn đoán (DIQ010)', positive_rate_test: 0.168 },
      threshold: 0.5,
      metrics_test: { roc_auc: 0.949, f1_pos: 0.726, recall_pos: 0.891, precision_pos: 0.612 },
      baseline: null, selection_rule: null, limitations: []
    },
    {
      kind: 'brfss', name: 'BRFSS (khảo sát lối sống)', architecture: 'MLP', available: true,
      dataset: { name: 'BRFSS (CDC)', label: 'Tự khai đã từng được chẩn đoán', n_train: 418492, positive_rate_test: 0.143 },
      threshold: 0.5,
      metrics_test: { roc_auc: 0.764, f1_pos: 0.382, recall_pos: 0.757, precision_pos: 0.256, accuracy: 0.65 },
      baseline: null, selection_rule: null, limitations: []
    },
    {
      kind: 'symptoms', name: 'UCI (triệu chứng)', architecture: 'MLP', available: true,
      dataset: { name: 'UCI Early Stage Diabetes', positive_rate_test: 0.686 },
      threshold: 0.5,
      metrics_test: { roc_auc: 0.923, f1_pos: 0.833, recall_pos: 0.714, precision_pos: 1 },
      baseline: null, selection_rule: null, limitations: []
    }
  ],
  rl: { episodes_per_seed: 200, seeds: 5, results: [
    { policy: 'DQN', mean_return: 2.026, std_return: 0.042 },
    { policy: 'Luật tham lam', mean_return: 2.03 },
    { policy: 'Ngẫu nhiên', mean_return: 0.93 },
    { policy: 'Tối ưu', mean_return: 2.03 }
  ] },
  assistant: { llm: 'qwen3:4b-instruct', llm_provider: 'Ollama', embedding: 'bge-m3', embedding_dim: 1024,
    top_k: 3, min_cosine: 0.53, vector_index: false, number_guard: 'v2' },
  kb: {
    reviewed_chunks: 61, reviewed_docs: 45, web_chunks: 190, web_pages: 25, topics: 79, entities: 48, relations: 53,
    relations_by_type: [
      { type: 'INCREASES_RISK_OF', count: 9 }, { type: 'DIAGNOSES', count: 8 }, { type: 'REDUCES_RISK_OF', count: 8 },
      { type: 'HAS_SYMPTOM', count: 8 }, { type: 'CAN_CAUSE', count: 8 }, { type: 'MONITORED_BY', count: 5 },
      { type: 'IS_A', count: 3 }, { type: 'CAUSES', count: 2 }, { type: 'PROGRESSES_TO', count: 1 }, { type: 'TREATS', count: 1 }
    ],
    topic_names: ['HbA1c', 'Đường huyết lúc đói', 'Tiền đái tháo đường', 'Chăm sóc bàn chân', 'Vận động thể lực'],
    reviewed_sources: [
      { title: 'Bộ Y tế Việt Nam: Hướng dẫn chẩn đoán và điều trị đái tháo đường típ 2', url: 'https://benhviendakhoabaria.vn/', publisher: null, topic: 'Chẩn đoán', date: '2026-11-12' },
      { title: 'Tiêu chuẩn chẩn đoán đái tháo đường (ADA 2026)', url: 'https://pmc.ncbi.nlm.nih.gov/', publisher: 'ADA', topic: 'Chẩn đoán', date: '2026-11-12' },
      { title: 'HbA1c là gì?', url: 'https://www.niddk.nih.gov/', publisher: null, topic: 'HbA1c', date: '2026-11-10' },
      { title: 'WHO: Diabetes fact sheet', url: 'https://www.who.int/', publisher: 'WHO', topic: 'Tổng quan', date: '2026-11-08' },
      { title: 'Hướng dẫn chăm sóc bàn chân', url: 'https://example.org/foot', publisher: null, topic: 'Chăm sóc bàn chân', date: null }
    ]
  },
  limitations: []
};

/** Biến thể cho ảnh chụp/kiểm thử trạng thái (3a-2). */
export function aboutFixtureVariant(name: string): AboutInfo {
  if (name === 'kbdown') return { ...ABOUT_FIXTURE, kb: null };
  if (name === 'partial') {
    return { ...ABOUT_FIXTURE, rl: null, models: ABOUT_FIXTURE.models!.map((m, i) => (i === 3 ? { ...m, metrics_test: null } : m)) };
  }
  return ABOUT_FIXTURE;
}
