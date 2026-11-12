export type NumberField = { key: string; label: string; min: number; max: number; step: string; unit: string; hint?: string };

const f = (key: string, label: string, min: number, max: number, step: string, unit: string, hint?: string): NumberField =>
  ({ key, label, min, max, step, unit, hint });

export const nhanes15Groups: { legend: string; fields: NumberField[] }[] = [
  { legend: 'Thông tin chung', fields: [f('RIDAGEYR', 'Tuổi (năm)', 18, 80, '1', 'tuổi')] },
  {
    legend: 'Cơ thể',
    fields: [
      f('BMXWT', 'Cân nặng (kg)', 20, 350, '0.1', 'kg'),
      f('BMXHT', 'Chiều cao (cm)', 100, 250, '0.1', 'cm'),
      f('BMXWAIST', 'Vòng eo (cm)', 30, 250, '0.1', 'cm')
    ]
  },
  {
    legend: 'Huyết áp',
    fields: [
      f('BPXSY1', 'Huyết áp tâm thu (mmHg)', 50, 300, '1', 'mmHg'),
      f('BPXDI1', 'Huyết áp tâm trương (mmHg)', 20, 200, '1', 'mmHg')
    ]
  },
  {
    legend: 'Xét nghiệm máu',
    fields: [
      f('LBXGLU', 'Glucose huyết tương lúc đói (mg/dL)', 40, 500, '0.1', 'mg/dL', 'Đo khi nhịn ăn ít nhất 8 giờ. Từ 40 đến 500 mg/dL'),
      f('LBXGH', 'HbA1c (%)', 3, 20, '0.1', '%', 'Đường huyết trung bình 2-3 tháng, ghi trên phiếu xét nghiệm. Từ 3 đến 20 %'),
      f('LBXTC', 'Cholesterol toàn phần (mg/dL)', 50, 800, '0.1', 'mg/dL'),
      f('LBDHDD', 'HDL cholesterol (mg/dL)', 5, 200, '0.1', 'mg/dL'),
      f('LBXTR', 'Triglyceride (mg/dL)', 10, 3000, '0.1', 'mg/dL', 'Mỡ máu, từ 10 đến 3000 mg/dL'),
      f('LBXSATSI', 'ALT (U/L)', 1, 1000, '0.1', 'U/L', 'Men gan, từ 1 đến 1000 U/L'),
      f('LBXSCR', 'Creatinine huyết thanh (mg/dL)', 0.1, 15, '0.01', 'mg/dL', 'Chỉ số chức năng thận, từ 0,1 đến 15 mg/dL')
    ]
  }
];

export const nhanesBasicFields: NumberField[] = [
  f('RIDAGEYR', 'Tuổi (năm)', 18, 80, '1', 'tuổi'),
  f('BMXBMI', 'BMI (kg/m²)', 10, 100, '0.1', 'kg/m²'),
  f('LBXGLU', 'Glucose huyết tương lúc đói (mg/dL)', 40, 500, '0.1', 'mg/dL', 'Đo khi nhịn ăn ít nhất 8 giờ. Từ 40 đến 500 mg/dL'),
  f('LBXGH', 'HbA1c (%)', 3, 20, '0.1', '%', 'Đường huyết trung bình 2-3 tháng, ghi trên phiếu xét nghiệm. Từ 3 đến 20 %')
];

const vn = (n: number) => n.toLocaleString('vi-VN');
export const fieldHint = (x: NumberField) => x.hint ?? `Từ ${vn(x.min)} đến ${vn(x.max)} ${x.unit}`;
