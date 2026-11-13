"""Sinh các notebook nâng cấp dữ liệu (07, 08, 09) từ notebook gốc 02 và 04.

Giữ nguyên quy trình đã kiểm chứng của notebook gốc (tiền xử lý fit trên train,
3 seed, chọn mô hình theo ROC-AUC validation, ngưỡng theo F1 validation, bootstrap
trên test), chỉ thay phần: giới thiệu, cấu hình, đọc dữ liệu, làm sạch/chia tập,
và thêm một cell đánh giá độ quan trọng đặc trưng (permutation importance).

Chạy:  .venv/bin/python notebooks/training/_tao_notebook_v2.py
"""
import copy
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def code(src: str) -> dict:
    return {'cell_type': 'code', 'execution_count': None, 'metadata': {}, 'outputs': [], 'source': src.strip('\n')}


def md(src: str) -> dict:
    return {'cell_type': 'markdown', 'metadata': {}, 'source': src.strip('\n')}


def setup_cell(base_src: str, experiment: str, model_type: str, purpose: str) -> dict:
    lines = base_src.split('\n')
    lines[0] = f"EXPERIMENT = '{experiment}'"
    lines[1] = f"MODEL_TYPE = '{model_type}'"
    lines[2] = f"PURPOSE = '{purpose}'"
    return code('\n'.join(lines))


IMPORTANCE = code(r'''
# Độ quan trọng đặc trưng (permutation importance) trên VALIDATION cho mô hình đã chọn.
# Xáo trộn từng cột gốc rồi đo ROC-AUC giảm bao nhiêu: giảm càng nhiều, mô hình càng dựa vào biến đó.
# Đây là mức độ mô hình sử dụng biến, KHÔNG phải quan hệ nhân quả.
def score_frame(frame):
    X = preprocessor.transform(frame_x(frame)).astype('float32')
    if selected.startswith('neural_seed_'):
        with torch.no_grad(): return torch.sigmoid(best_run['model'](torch.tensor(X))).numpy()
    return candidates[selected].predict_proba(X)[:, 1]
if selected.startswith('neural_seed_'):
    best_run = next(r for r in runs if selected == f"neural_seed_{r['seed']}")
sample = val.sample(n=min(20000, len(val)), random_state=SEED)
y_sample = sample['class'].to_numpy()
base_auc = roc_auc_score(y_sample, score_frame(sample))
rng_imp = np.random.default_rng(SEED)
importance = {}
for col in features:
    drops = []
    for _ in range(1 if SMOKE else 3):
        shuffled = sample.copy()
        shuffled[col] = rng_imp.permutation(shuffled[col].to_numpy())
        drops.append(base_auc - roc_auc_score(y_sample, score_frame(shuffled)))
    importance[col] = float(np.mean(drops))
importance = dict(sorted(importance.items(), key=lambda kv: kv[1], reverse=True))
print(f'ROC-AUC gốc trên mẫu validation: {base_auc:.4f}')
print(pd.Series(importance, name='AUC giảm khi xáo trộn').round(4).to_string())
pd.Series(importance).iloc[::-1].plot.barh(figsize=(7, max(3, len(features) * .32)), title=f'Permutation importance — {selected} (validation)')
plt.xlabel('ROC-AUC giảm'); plt.tight_layout(); plt.show()
''')

SAVE_IMPORTANCE = code(r'''
# Ghi thêm độ quan trọng đặc trưng và mô tả biến vào report.json của lần chạy.
report_path = RUN_DIR / 'report.json'
saved = json.loads(report_path.read_text(encoding='utf-8'))
saved['permutation_importance_validation'] = importance
saved['feature_descriptions'] = FEATURE_DESCRIPTIONS
saved.update(EXTRA_REPORT)
report_path.write_text(json.dumps(saved, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
print('Đã cập nhật', report_path)
''')


# ---------------------------------------------------------------- BRFSS
BRFSS_COMMON_DESC = {
    '_BMI5': 'BMI (kg/m²)', '_AGEG5YR': 'Nhóm tuổi 5 năm (1=18–24 … 13=80+)', 'SEXVAR': 'Giới (1 nam, 2 nữ)',
    '_SMOKER3': 'Hút thuốc (1–2 hiện tại, 3 đã bỏ, 4 chưa từng)', '_TOTINDA': 'Vận động ngoài công việc 30 ngày qua (1 có, 2 không)',
    'GENHLTH': 'Tự đánh giá sức khỏe chung (1 rất tốt … 5 kém)', '_PHYS14D': 'Số ngày sức khỏe thể chất kém (1: 0, 2: 1–13, 3: 14+)',
    '_MENT14D': 'Số ngày sức khỏe tinh thần kém (1: 0, 2: 1–13, 3: 14+)', 'DIFFWALK': 'Khó khăn đi bộ/leo cầu thang (1 có, 2 không)',
    'CVDSTRK3': 'Từng được báo đột quỵ (1 có, 2 không)', '_MICHD': 'Từng bệnh mạch vành/nhồi máu (1 có, 2 không)',
    'CHCKDNY2': 'Từng được báo bệnh thận (1 có, 2 không)', 'CHCCOPD3': 'Từng được báo COPD (1 có, 2 không)',
    'ADDEPEV3': 'Từng được báo trầm cảm (1 có, 2 không)', 'HEAVY_DRINK': 'Uống rượu nhiều (1 không, 2 có); 2021 _RFDRHV7, 2022–23 _RFDRHV8',
    'HLTHPLAN': 'Có bảo hiểm y tế (1 có, 2 không); 2021–22 _HLTHPLN, 2023 _HLTHPL1', 'MEDCOST1': 'Không đi khám được vì chi phí (1 có, 2 không)',
    'CHECKUP1': 'Lần khám tổng quát gần nhất (1 <1 năm … 4 ≥5 năm, 8 chưa bao giờ)', '_EDUCAG': 'Học vấn (1–4)', '_INCOMG1': 'Nhóm thu nhập (1–7)',
    '_RFHYPE6': 'Từng được báo tăng huyết áp (1 không, 2 có) — chỉ có ở năm lẻ', '_RFCHOL3': 'Từng được báo cholesterol cao (1 không, 2 có) — chỉ có ở năm lẻ',
}
BRFSS_CODES = {
    '_AGEG5YR': list(range(1, 14)), 'SEXVAR': [1, 2], '_SMOKER3': [1, 2, 3, 4], '_TOTINDA': [1, 2],
    'GENHLTH': [1, 2, 3, 4, 5], '_PHYS14D': [1, 2, 3], '_MENT14D': [1, 2, 3], 'DIFFWALK': [1, 2], 'CVDSTRK3': [1, 2],
    '_MICHD': [1, 2], 'CHCKDNY2': [1, 2], 'CHCCOPD3': [1, 2], 'ADDEPEV3': [1, 2], 'HEAVY_DRINK': [1, 2], 'HLTHPLAN': [1, 2],
    'MEDCOST1': [1, 2], 'CHECKUP1': [1, 2, 3, 4, 8], '_EDUCAG': [1, 2, 3, 4], '_INCOMG1': list(range(1, 8)),
    '_RFHYPE6': [1, 2], '_RFCHOL3': [1, 2],
}


def brfss_cells(features: list[str], years_train: list[int], intro: str, extra_report: dict) -> dict:
    load = f'''
import pyreadstat
features = {features!r}
numeric, categorical = ['_BMI5'], [c for c in features if c != '_BMI5']
FEATURE_DESCRIPTIONS = {{k: v for k, v in {BRFSS_COMMON_DESC!r}.items() if k in features}}
EXTRA_REPORT = {extra_report!r}
# Một số biến đổi tên giữa các năm: gộp về cùng một tên (đã đối chiếu codebook CDC từng năm).
RENAMES = {{2021: {{'_RFDRHV7': 'HEAVY_DRINK', '_HLTHPLN': 'HLTHPLAN'}},
           2022: {{'_RFDRHV8': 'HEAVY_DRINK', '_HLTHPLN': 'HLTHPLAN'}},
           2023: {{'_RFDRHV8': 'HEAVY_DRINK', '_HLTHPL1': 'HLTHPLAN'}}}}
YEARS = {years_train + [2023]!r}  # năm cuối là tập test theo thời gian
source_paths = [ROOT/f'data/raw/LLCP{{year}}.XPT' for year in YEARS]
def read_survey(path, year):
    inverse = {{new: old for old, new in RENAMES[year].items()}}
    usecols = [inverse.get(c, c) for c in features] + ['DIABETE4']
    kwargs = {{'row_limit': 12000}} if SMOKE else {{}}
    frame, _ = pyreadstat.read_xport(str(path), usecols=usecols, encoding='latin1', **kwargs)
    missing = set(usecols) - set(frame.columns)
    if missing: raise ValueError(f'{{year}} thiếu cột {{sorted(missing)}}; kiểm tra codebook trước khi đổi danh sách biến')
    return frame.rename(columns=RENAMES[year])
raw = [read_survey(path, year) for path, year in zip(source_paths, YEARS)]
print('Số dòng gốc đọc từng năm:', dict(zip(YEARS, [len(x) for x in raw])))
'''
    clean = f'''
codes = {{k: v for k, v in {BRFSS_CODES!r}.items() if k in features}}
def clean_survey(frame):
    # Nhãn DIABETE4: 1 = từng được báo mắc ĐTĐ, 3 = không. Loại 2 (thai kỳ), 4 (tiền ĐTĐ), 7/9/trống.
    df = frame[frame.DIABETE4.isin([1, 3])].copy()
    df['class'] = df.DIABETE4.map({{1: 1, 3: 0}})
    df['_BMI5'] = (pd.to_numeric(df['_BMI5'], errors='coerce') / 100).where(lambda x: x.between(10, 100))
    for col, valid in codes.items():
        values = pd.to_numeric(df[col], errors='coerce')
        # Mã 7/9 (không biết/từ chối) và trống trở thành thiếu, được impute bằng giá trị hay gặp nhất của train.
        df[col] = values.where(values.isin(valid)).astype('Int64').astype('string')
    return df[features + ['class']]
frames = [clean_survey(frame) for frame in raw]
trainval, test = pd.concat(frames[:-1], ignore_index=True), frames[-1]
train, val = train_test_split(trainval, test_size=0.2, stratify=trainval['class'], random_state=SEED)
print('Sau lọc nhãn theo năm:', dict(zip(YEARS, [len(f) for f in frames])))
print('Tỷ lệ nhãn 1 theo năm:', dict(zip(YEARS, [round(float(f["class"].mean()), 4) for f in frames])))
'''
    return {'intro': intro, 'load': load, 'clean': clean}


# ---------------------------------------------------------------- NHANES
NHANES_LOAD = r'''
features = ['RIDAGEYR','RIAGENDR','BMXBMI','BMXWAIST','BPXSY1','BPXDI1','LBXGLU','LBXGH','LBXTC','LBDHDD','LBXTR','LBXSATSI','LBXSCR','BMXWT','BMXHT']
numeric, categorical = features, []
FEATURE_DESCRIPTIONS = {'RIDAGEYR':'Tuổi (năm)','RIAGENDR':'Giới (1 nam, 2 nữ)','BMXBMI':'BMI (kg/m²)','BMXWAIST':'Vòng eo (cm)',
  'BPXSY1':'Huyết áp tâm thu lần 1 (mmHg)','BPXDI1':'Huyết áp tâm trương lần 1 (mmHg)','LBXGLU':'Glucose huyết tương lúc đói (mg/dL)',
  'LBXGH':'HbA1c (%)','LBXTC':'Cholesterol toàn phần (mg/dL)','LBDHDD':'HDL (mg/dL)','LBXTR':'Triglyceride (mg/dL)',
  'LBXSATSI':'ALT (U/L)','LBXSCR':'Creatinine huyết thanh (mg/dL)','BMXWT':'Cân nặng (kg)','BMXHT':'Chiều cao (cm)'}
columns = {
 'DEMO':['SEQN','RIDAGEYR','RIAGENDR','SDMVSTRA','SDMVPSU'], 'DIQ':['SEQN','DIQ010'],
 'BMX':['SEQN','BMXBMI','BMXWAIST','BMXWT','BMXHT'], 'BPX':['SEQN','BPXSY1','BPXDI1'],
 'GLU':['SEQN','LBXGLU'], 'GHB':['SEQN','LBXGH'], 'TCHOL':['SEQN','LBXTC'],
 'HDL':['SEQN','LBDHDD'], 'TRIGLY':['SEQN','LBXTR'], 'BIOPRO':['SEQN','LBXSATSI','LBXSCR']}
# Chu kỳ 2021–2023 (_L): huyết áp đo bằng máy dao động tự động (BPXO) thay cho đo thủ công,
# triglyceride đổi tên LBXTLG. Đổi tên về cùng tên biến nhưng phương pháp đo KHÁC — chỉ dùng làm test ngoài.
CYCLE_FILES = {'L': {'BPX': ('BPXO', {'BPXOSY1': 'BPXSY1', 'BPXODI1': 'BPXDI1'}), 'TRIGLY': ('TRIGLY', {'LBXTLG': 'LBXTR'})}}
CYCLES = {'G': '2011–2012', 'H': '2013–2014', 'I': '2015–2016', 'J': '2017–2018', 'L': '2021–2023'}
TRAIN_CYCLES, TEST_CYCLE, EXTERNAL_CYCLE = ['G', 'H', 'I'], 'J', 'L'
EXTRA_REPORT = {'cycles': CYCLES, 'train_validation_cycles': TRAIN_CYCLES, 'test_cycle': TEST_CYCLE, 'external_test_cycle': EXTERNAL_CYCLE}
source_paths = []
def read_cycle(suffix):
    frames=[]
    for name, cols in columns.items():
        file_name, renames = CYCLE_FILES.get(suffix, {}).get(name, (name, {}))
        path=ROOT/f'data/raw/nhanes/{file_name}_{suffix}.xpt'; source_paths.append(path)
        f=pd.read_sas(path,format='xport').rename(columns=renames)[cols]
        if f.SEQN.duplicated().any(): raise ValueError(f'Trùng SEQN: {path}')
        frames.append(f)
    df=frames[0]
    for f in frames[1:]: df=df.merge(f,on='SEQN',how='left',validate='one_to_one')
    df['cycle']=suffix
    return df
raw = {s: read_cycle(s) for s in TRAIN_CYCLES + [TEST_CYCLE, EXTERNAL_CYCLE]}
print('Số dòng gốc theo chu kỳ:', {CYCLES[s]: len(df) for s, df in raw.items()})
'''

NHANES_CLEAN = r'''
def clean_cycle(raw):
    df=raw[(raw.RIDAGEYR>=18)&raw.DIQ010.isin([1,2])].copy()
    for col in ['BPXSY1','BPXDI1']:
        if col in df: df.loc[df[col] <= 0,col] = np.nan
    df = df.dropna(subset=features+['SDMVSTRA','SDMVPSU']).copy()
    df['class'] = (df.DIQ010 == 1).astype(int)
    # Nhóm theo chu kỳ + tầng + PSU để train/validation không chia cắt cùng một cụm khảo sát.
    df['group'] = df.cycle+'_'+df.SDMVSTRA.astype(str)+'_'+df.SDMVPSU.astype(str)
    return df
cleaned = {s: clean_cycle(df) for s, df in raw.items()}
old = pd.concat([cleaned[s] for s in TRAIN_CYCLES], ignore_index=True)
test, external = cleaned[TEST_CYCLE], cleaned[EXTERNAL_CYCLE]
all_seqn = [set(df.SEQN) for df in cleaned.values()]
if sum(len(s) for s in all_seqn) != len(set().union(*all_seqn)): raise ValueError('SEQN trùng giữa các chu kỳ; cần kiểm tra.')
indices = GroupShuffleSplit(n_splits=1,test_size=0.2,random_state=SEED)
a,b = next(indices.split(old,old['class'],groups=old.group))
train,val = old.iloc[a].copy(),old.iloc[b].copy()
assert set(train.group).isdisjoint(set(val.group))
print('Mẫu đủ 15 chỉ số theo chu kỳ:', {CYCLES[s]: (len(df), int(df['class'].sum())) for s, df in cleaned.items()}, '(tổng, số nhãn 1)')
print('Train+validation (2011–2016):', len(old), '| test 2017–2018:', len(test), '| test ngoài 2021–2023:', len(external))
'''

NHANES_EXTERNAL = code(r'''
# Test ngoài theo thời gian: chu kỳ 2021–2023, khác phương pháp đo huyết áp. Dùng đúng mô hình, bộ tiền xử lý và ngưỡng đã chọn.
X_ext = preprocessor.transform(frame_x(external)).astype('float32'); y_ext = external['class'].to_numpy()
if selected.startswith('neural_seed_'):
    with torch.no_grad(): ext_scores = torch.sigmoid(best_run['model'](torch.tensor(X_ext))).numpy()
else: ext_scores = candidates[selected].predict_proba(X_ext)[:, 1]
external_metrics = {**threshold_scores(y_ext, ext_scores, selected_threshold), 'n': int(len(y_ext)), 'positives': int(y_ext.sum()),
    'confusion_matrix': confusion_matrix(y_ext, (ext_scores >= selected_threshold).astype(int), labels=[0, 1]).tolist()}
print('Test ngoài 2021–2023:', json.dumps(external_metrics, indent=2))
EXTRA_REPORT['external_test_2021_2023'] = external_metrics
''')


def build(base_name: str, out_name: str, intro: str, setup_args: tuple, load: str, clean: str, extra_cells: list | None = None) -> None:
    nb = json.loads((HERE / base_name).read_text(encoding='utf-8'))
    cells = copy.deepcopy(nb['cells'])
    for cell in cells:
        if cell['cell_type'] == 'code':
            cell['outputs'] = []; cell['execution_count'] = None
    cells[0] = md(intro)
    cells[2] = setup_cell(''.join(nb['cells'][2]['source']), *setup_args)
    cells[4] = code(load)
    cells[6] = code(clean)
    # Batch lớn cho mọi biến thể BRFSS (hàng trăm nghìn mẫu)
    src14 = ''.join(cells[14]['source']).replace("EXPERIMENT=='brfss'", "EXPERIMENT.startswith('brfss')")
    cells[14]['source'] = src14
    tail = [md('## 9b. Độ quan trọng đặc trưng\nMô hình đã chọn dựa vào biến nào nhiều nhất? Đo trên validation, không dùng test.'), IMPORTANCE]
    tail += extra_cells or []
    # chèn sau cell đánh giá test (18), trước phần lưu (19, 20); thêm cell ghi report sau cùng
    cells = cells[:19] + tail + cells[19:21] + [SAVE_IMPORTANCE] + cells[21:]
    nb['cells'] = cells
    (HERE / out_name).write_text(json.dumps(nb, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    print('wrote', out_name)


BRFSS20 = ['_BMI5', '_AGEG5YR', 'SEXVAR', '_SMOKER3', '_TOTINDA', 'GENHLTH', '_PHYS14D', '_MENT14D', 'DIFFWALK',
           'CVDSTRK3', '_MICHD', 'CHCKDNY2', 'CHCCOPD3', 'ADDEPEV3', 'HEAVY_DRINK', 'HLTHPLAN', 'MEDCOST1', 'CHECKUP1',
           '_EDUCAG', '_INCOMG1']
BRFSS22 = BRFSS20 + ['_RFHYPE6', '_RFCHOL3']

if __name__ == '__main__':
    a = brfss_cells(BRFSS20, [2021, 2022],
        '''# BRFSS mở rộng — 20 biến, cùng phép chia với notebook 02

Nâng cấp notebook 02 (chỉ 5 biến, ROC-AUC test 0,76). Dùng **cùng 3 file BRFSS 2021–2023 đã tải**, cùng phép chia (2021–22 train/validation, 2023 test theo thời gian), nhưng khai thác thêm 15 biến có mặt ở cả ba năm: sức khỏe tự đánh giá, khó khăn đi lại, bệnh kèm (đột quỵ, mạch vành, thận, COPD, trầm cảm), rượu, bảo hiểm, chi phí khám, học vấn, thu nhập. Bộ biến tương tự bộ *CDC Diabetes Health Indicators* (UCI id 891).

Lưu ý: nhiều biến là **bệnh kèm có thể xuất hiện sau khi mắc đái tháo đường** (nhân quả ngược), nên mô hình phân loại trạng thái hiện tại tốt hơn nhưng không phải dự báo mắc mới. BRFSS là khảo sát Hoa Kỳ tự khai, không dùng survey weight. Chỉ dùng cho học thuật.''',
        {'variant': 'A_all_years_20_features', 'comparison_baseline': 'notebook 02 (5 features), same split'})
    build('02_BRFSS_Khao_Sat.ipynb', '07_BRFSS_20_Bien.ipynb', a['intro'],
          ('brfss20', 'MLP', 'BRFSS 2021–2023, 20 biến có ở cả ba năm; nhãn tự khai từng được báo mắc ĐTĐ; không dùng survey weight.'),
          a['load'], a['clean'])

    b = brfss_cells(BRFSS22, [2021],
        '''# BRFSS năm lẻ — 22 biến, thêm tăng huyết áp và cholesterol cao

Câu hỏi tăng huyết áp (`_RFHYPE6`) và cholesterol (`_RFCHOL3`) chỉ có trong BRFSS năm lẻ, nên notebook này **train/validation trên 2021 và test trên 2023**. Đây là hai yếu tố nguy cơ quan trọng của đái tháo đường típ 2 theo ADA. So sánh với notebook 07 để thấy giá trị thêm của hai biến (nhưng tập train khác nên so sánh chỉ mang tính tham khảo).

Cùng các giới hạn với notebook 07: dữ liệu tự khai, cắt ngang, nhân quả ngược với bệnh kèm, không dùng survey weight, không phải dữ liệu Việt Nam.''',
        {'variant': 'B_odd_years_22_features', 'comparison_baseline': 'notebook 07 (20 features, trained 2021–22)'})
    build('02_BRFSS_Khao_Sat.ipynb', '08_BRFSS_22_Bien_Huyet_Ap.ipynb', b['intro'],
          ('brfss22', 'MLP', 'BRFSS 2021 train, 2023 test; 22 biến gồm tăng huyết áp và cholesterol cao; nhãn tự khai; không dùng survey weight.'),
          b['load'], b['clean'])

    build('04_NHANES_15_Chi_So.ipynb', '09_NHANES15_Nhieu_Chu_Ky.ipynb',
        '''# NHANES 15 chỉ số — mở rộng 5 chu kỳ (2011–2023)

Nâng cấp notebook 04 (chỉ 2 chu kỳ, train 2015–16). Tải thêm các chu kỳ công khai của CDC: **2011–2012 (G), 2013–2014 (H)** và **2021–2023 (L)**.

- Train/validation: 2011–2016 (G, H, I), chia theo cụm khảo sát (chu kỳ + tầng + PSU) để tránh rò rỉ.
- Test: 2017–2018 (J) — cùng tập test với notebook 04 để so sánh trực tiếp.
- Test ngoài: 2021–2023 (L) — dữ liệu sau COVID, huyết áp đo bằng máy tự động (khác phương pháp), dùng để kiểm tra độ bền theo thời gian.

Nhãn DIQ010 là tự khai từng được thông báo mắc đái tháo đường; glucose/HbA1c có thể đã dùng để chẩn đoán trước đó. Không phải chẩn đoán hay dự báo mắc mới; không phải dữ liệu Việt Nam.''',
        ('nhanes15_multi', 'CNN', 'NHANES 2011–2016 train, 2017–2018 test, 2021–2023 test ngoài; 15 chỉ số; nhãn tự khai DIQ010.'),
        NHANES_LOAD, NHANES_CLEAN, [md('## 9c. Test ngoài 2021–2023\nĐánh giá thêm trên chu kỳ mới nhất, không tham gia chọn mô hình hay ngưỡng.'), NHANES_EXTERNAL])
