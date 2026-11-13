"""Sinh notebook 11 (BRFSS 2015-2023, ~3,9 triệu dòng) từ notebook gốc 02, dùng lại các helper của _tao_notebook_v2.py.

Chạy:  .venv/bin/python notebooks/training/_tao_notebook_11.py
"""
import json
from pathlib import Path

import _tao_notebook_v2 as v2
from _tao_notebook_v2 import BRFSS_CODES, HERE, build, code, md

FEATURES = ['_BMI5', '_AGEG5YR', 'SEXVAR', '_SMOKER3', '_TOTINDA', 'GENHLTH', '_PHYS14D', '_MENT14D', 'DIFFWALK',
            'CVDSTRK3', '_MICHD', 'CHCKDNY2', 'CHCCOPD3', 'ADDEPEV3', 'HEAVY_DRINK', 'HLTHPLAN', 'MEDCOST1', 'CHECKUP1',
            '_EDUCAG', 'INCOMG5']

# harmonized name -> [((first_year, last_year), source column in that year's XPT)]. None = suy ra từ biến khác (xem DERIVED).
SPANS = {
    '_BMI5': [((2015, 2023), '_BMI5')],
    '_AGEG5YR': [((2015, 2023), '_AGEG5YR')],
    'SEXVAR': [((2015, 2017), 'SEX'), ((2018, 2018), 'SEX1'), ((2019, 2023), 'SEXVAR')],
    '_SMOKER3': [((2015, 2023), '_SMOKER3')],
    '_TOTINDA': [((2015, 2023), '_TOTINDA')],
    'GENHLTH': [((2015, 2023), 'GENHLTH')],
    '_PHYS14D': [((2015, 2015), None), ((2016, 2023), '_PHYS14D')],
    '_MENT14D': [((2015, 2015), None), ((2016, 2023), '_MENT14D')],
    'DIFFWALK': [((2015, 2023), 'DIFFWALK')],
    'CVDSTRK3': [((2015, 2023), 'CVDSTRK3')],
    '_MICHD': [((2015, 2023), '_MICHD')],
    'CHCKDNY2': [((2015, 2017), 'CHCKIDNY'), ((2018, 2018), 'CHCKDNY1'), ((2019, 2023), 'CHCKDNY2')],
    'CHCCOPD3': [((2015, 2018), 'CHCCOPD1'), ((2019, 2020), 'CHCCOPD2'), ((2021, 2023), 'CHCCOPD3')],
    'ADDEPEV3': [((2015, 2018), 'ADDEPEV2'), ((2019, 2023), 'ADDEPEV3')],
    'HEAVY_DRINK': [((2015, 2017), '_RFDRHV5'), ((2018, 2018), '_RFDRHV6'), ((2019, 2021), '_RFDRHV7'), ((2022, 2023), '_RFDRHV8')],
    'HLTHPLAN': [((2015, 2020), 'HLTHPLN1'), ((2021, 2022), '_HLTHPLN'), ((2023, 2023), '_HLTHPL1')],
    'MEDCOST1': [((2015, 2020), 'MEDCOST'), ((2021, 2023), 'MEDCOST1')],
    'CHECKUP1': [((2015, 2023), 'CHECKUP1')],
    '_EDUCAG': [((2015, 2023), '_EDUCAG')],
    'INCOMG5': [((2015, 2020), '_INCOMG'), ((2021, 2023), '_INCOMG1')],
}
# Nhóm biến năm thì khác tên: hỏng nếu thiếu cột. Các biến điều tra chỉ năm lẻ bị loại khỏi bộ chung:
DROPPED = {'_RFHYPE5/_RFHYPE6 (tăng huyết áp)': 'chỉ có 2015, 2017, 2019, 2021, 2023',
           '_RFCHOL1/_RFCHOL2/_RFCHOL3 (cholesterol cao)': 'chỉ có 2017, 2019, 2021, 2023'}
CODEBOOKS = {
    2015: 'https://www.cdc.gov/brfss/annual_data/2015/pdf/codebook15_llcp.pdf',
    2016: 'https://www.cdc.gov/brfss/annual_data/2016/pdf/codebook16_llcp.pdf',
    2017: 'https://www.cdc.gov/brfss/annual_data/2017/pdf/codebook17_llcp-v2-508.pdf',
    2018: 'https://www.cdc.gov/brfss/annual_data/2018/pdf/codebook18_llcp-v2-508.pdf',
    2019: 'https://www.cdc.gov/brfss/annual_data/2019/pdf/codebook19_llcp-v2-508.HTML',
    2020: 'https://www.cdc.gov/brfss/annual_data/2020/pdf/codebook20_llcp-v2-508.pdf',
    2021: 'https://www.cdc.gov/brfss/annual_data/2021/pdf/codebook21_llcp-v2-508.pdf',
    2022: 'https://www.cdc.gov/brfss/annual_data/2022/zip/codebook22_llcp-v2-508.zip',
    2023: 'https://www.cdc.gov/brfss/annual_data/2023/zip/codebook23_llcp-v2-508.zip',
}
CODES = dict(BRFSS_CODES)
for k in ('_RFHYPE6', '_RFCHOL3', 'HLTHPLAN'):
    CODES.pop(k, None)
CODES['HLTHPLAN'] = [1, 2]
CODES['CHCKDNY2'] = [1, 2]
CODES['INCOMG5'] = [1, 2, 3, 4, 5]
CODES.pop('_INCOMG1', None)
DESC = dict(v2.BRFSS_COMMON_DESC)
DESC.pop('_RFHYPE6', None); DESC.pop('_RFCHOL3', None); DESC.pop('_INCOMG1', None)
DESC['INCOMG5'] = 'Nhóm thu nhập gộp 5 mức (1 <15k USD … 5 ≥50k USD)'
DESC['HLTHPLAN'] = 'Có bảo hiểm/độ bao phủ y tế (1 có, 2 không); 2023 theo định nghĩa _HLTHPL1 (PRIMINS1)'
DESC['_PHYS14D'] = 'Số ngày sức khỏe thể chất kém (1: 0, 2: 1–13, 3: 14+); 2015 suy ra từ PHYSHLTH'
DESC['_MENT14D'] = 'Số ngày sức khỏe tinh thần kém (1: 0, 2: 1–13, 3: 14+); 2015 suy ra từ MENTHLTH'

INTRO = '''# BRFSS 2015–2023 — bộ dữ liệu lớn (khoảng 3,9 triệu dòng)

Mở rộng notebook 07 (BRFSS 2021–2023, 683 nghìn dòng train) sang **9 năm BRFSS 2015–2023** để xem thêm dữ liệu cũ có giúp mô hình dự đoán trạng thái "từng được báo mắc đái tháo đường" hay không.

**Phép chia theo thời gian (khác notebook 07).** Train 2015–2021, validation 2022, test 2023. Notebook 07 train/validation là chia ngẫu nhiên 80/20 của 2021–2022 (validation cùng năm với train), còn ở đây validation là một năm *tương lai* so với train. **Test 2023 giống hệt notebook 07** (cùng các dòng, cùng luật nhãn) để so sánh công bằng; nhưng validation khác nên ngưỡng và việc chọn mô hình cũng khác.

**Hài hoà biến.** BRFSS đổi tên/mã biến qua các năm. Bảng ánh xạ biến × năm nằm ở phần đọc dữ liệu. 20 biến của notebook 07 được giữ nguyên ý nghĩa; hai biến tăng huyết áp/cholesterol (chỉ có năm lẻ) bị bỏ. Chỉ khác 07 ở biến thu nhập: `_INCOMG` (5 mức, 2015–2020) và `_INCOMG1` (7 mức, 2021+) được gộp về 5 mức chung.

Nguồn dữ liệu: CDC BRFSS, https://www.cdc.gov/brfss/annual_data/annual_data.htm (tài liệu của chính phủ Hoa Kỳ, phạm vi công cộng). Codebook từng năm:
''' + '\n'.join(f'- {y}: {u}' for y, u in CODEBOOKS.items()) + '''

Giới hạn như notebook 07: tự khai, cắt ngang, nhân quả ngược với bệnh kèm, không dùng survey weight, dữ liệu Hoa Kỳ, chỉ dùng học thuật. Test 2023 đã được xem trong các lần chạy trước.'''

LOAD = r'''
import pyreadstat, time
NOTEBOOK_T0 = time.perf_counter()
features = __FEATURES__
numeric, categorical = ['_BMI5'], [c for c in features if c != '_BMI5']
FEATURE_DESCRIPTIONS = __DESC__
YEARS = list(range(2015, 2024))
TRAIN_YEARS, VAL_YEAR, TEST_YEAR = list(range(2015, 2022)), 2022, 2023
# Ánh xạ biến hài hoà -> cột nguồn trong XPT từng năm (đã đối chiếu codebook CDC + nhãn biến trong file XPT).
SPANS = __SPANS__
COLUMN_MAP = {h: {y: src for (a, b), src in spans for y in range(a, b + 1)} for h, spans in SPANS.items()}
assert all(set(m) == set(YEARS) for m in COLUMN_MAP.values()), 'Bảng ánh xạ phải phủ đủ 9 năm'
LABEL_SOURCE = {y: ('DIABETE3' if y <= 2018 else 'DIABETE4') for y in YEARS}
DROPPED = __DROPPED__
EXTRA_REPORT = {'variant': 'C_all_years_2015_2023_20_features', 'comparison_baseline': 'notebook 07 (cùng test 2023, validation khác)',
                'train_years': TRAIN_YEARS, 'validation_year': VAL_YEAR, 'test_year': TEST_YEAR,
                'column_map': {h: {str(y): s for y, s in m.items()} for h, m in COLUMN_MAP.items()},
                'label_source': {str(y): s for y, s in LABEL_SOURCE.items()}, 'dropped_variables': DROPPED,
                'codebooks': __CODEBOOKS__}
display_map = pd.DataFrame({h: {y: (s if s else 'suy ra (PHYSHLTH/MENTHLTH)') for y, s in m.items()} for h, m in COLUMN_MAP.items()}).T
display_map.loc['(nhãn) DIABETE'] = [LABEL_SOURCE[y] for y in YEARS]
print('Bảng ánh xạ biến hài hoà × cột nguồn trong XPT từng năm:'); print(display_map.to_string())
print('\nBiến bị bỏ vì không có ở mọi năm:', DROPPED)
source_paths = [ROOT/f'data/raw/LLCP{year}.XPT' for year in YEARS]
def days_level(days):
    # Suy ra _PHYS14D/_MENT14D như CDC: 88 = 0 ngày -> 1; 1–13 -> 2; 14–30 -> 3; không biết/từ chối/trống -> 9.
    days = pd.to_numeric(days, errors='coerce')
    level = pd.Series(9, index=days.index, dtype='int8')
    level[days == 88] = 1; level[days.between(1, 13)] = 2; level[days.between(14, 30)] = 3
    return level
DERIVED_CHECK = {}
def read_survey(year):
    source = {h: m[year] for h, m in COLUMN_MAP.items()}
    need = sorted({c for c in source.values() if c} | {LABEL_SOURCE[year], 'PHYSHLTH', 'MENTHLTH'})
    kwargs = {'row_limit': 12000} if SMOKE else {}
    frame, _ = pyreadstat.read_xport(str(ROOT/f'data/raw/LLCP{year}.XPT'), usecols=need, encoding='latin1', **kwargs)
    missing = set(need) - set(frame.columns)
    if missing: raise ValueError(f'{year} thiếu cột {sorted(missing)}; kiểm tra codebook trước khi đổi bảng ánh xạ')
    out = pd.DataFrame({'DIABETE': frame[LABEL_SOURCE[year]]})
    for h, col in source.items():
        out[h] = frame[col] if col else days_level(frame['PHYSHLTH' if h == '_PHYS14D' else 'MENTHLTH'])
    # Kiểm chứng công thức suy ra: ở các năm có biến chính thức, so với _PHYS14D/_MENT14D của CDC.
    for h, raw_col in (('_PHYS14D', 'PHYSHLTH'), ('_MENT14D', 'MENTHLTH')):
        if source[h]:
            same = (days_level(frame[raw_col]).to_numpy() == pd.to_numeric(frame[source[h]], errors='coerce').fillna(9).to_numpy())
            DERIVED_CHECK.setdefault(h, {})[year] = float(same.mean())
    out['year'] = year
    return out
raw = {year: read_survey(year) for year in YEARS}
print('\nSố dòng gốc đọc từng năm:', {y: len(f) for y, f in raw.items()}, '| tổng', sum(len(f) for f in raw.values()))
print('Công thức suy ra _PHYS14D/_MENT14D khớp biến chính thức của CDC (tỷ lệ dòng trùng, theo năm):')
print(pd.DataFrame(DERIVED_CHECK).round(5).to_string())
EXTRA_REPORT['derived_check'] = {h: {str(y): v for y, v in d.items()} for h, d in DERIVED_CHECK.items()}
'''

CLEAN = r'''
codes = __CODES__
def clean_survey(frame):
    # Nhãn: DIABETE = 1 (từng được báo mắc ĐTĐ) -> 1; 3 (không) -> 0. Loại 2 (chỉ khi mang thai), 4 (tiền ĐTĐ), 7/9 (không biết/từ chối), trống.
    df = frame[frame.DIABETE.isin([1, 3])].copy()
    df['class'] = df.DIABETE.map({1: 1, 3: 0}).astype('int8')
    df['_BMI5'] = (pd.to_numeric(df['_BMI5'], errors='coerce') / 100).where(lambda x: x.between(10, 100)).astype('float32')
    year = int(df['year'].iloc[0])
    if year >= 2021:  # _INCOMG1 7 mức -> 5 mức chung với _INCOMG: 50–<100k, 100–<200k, ≥200k đều thành "≥50k" (5)
        df['INCOMG5'] = pd.to_numeric(df['INCOMG5'], errors='coerce').replace({6: 5, 7: 5})
    for col, valid in codes.items():
        values = pd.to_numeric(df[col], errors='coerce')
        # Mã 7/9 (không biết/từ chối) và trống trở thành thiếu (NaN), được impute bằng giá trị hay gặp nhất của train.
        df[col] = values.where(values.isin(valid)).astype('float32')
    return df[features + ['class', 'year']].reset_index(drop=True)
frames = {year: clean_survey(frame) for year, frame in raw.items()}
del raw
print('Sau lọc nhãn theo năm:', {y: len(f) for y, f in frames.items()})
print('Tỷ lệ nhãn 1 theo năm:', {y: round(float(f['class'].mean()), 4) for y, f in frames.items()})
train = pd.concat([frames[y] for y in TRAIN_YEARS], ignore_index=True)
val, test = frames[VAL_YEAR].reset_index(drop=True), frames[TEST_YEAR].reset_index(drop=True)
del frames
EXTRA_REPORT['rows_after_label_filter_by_year'] = {str(y): int((train.year == y).sum()) for y in TRAIN_YEARS} | {str(VAL_YEAR): len(val), str(TEST_YEAR): len(test)}
EXTRA_REPORT['positive_rate_by_year'] = {str(y): float(train.loc[train.year == y, 'class'].mean()) for y in TRAIN_YEARS} | {str(VAL_YEAR): float(val['class'].mean()), str(TEST_YEAR): float(test['class'].mean())}
print(f'Train 2015–2021: {len(train):,} | validation 2022: {len(val):,} | test 2023: {len(test):,} | tổng {len(train)+len(val)+len(test):,}')
print('Bộ nhớ train (MB):', round(train.memory_usage(deep=True).sum() / 1e6, 1))
'''

PREPROC = r'''
def frame_x(frame): return frame[features]  # float32, thiếu = NaN; không sao chép sang object để tiết kiệm bộ nhớ
parts = [('num', make_pipeline(SimpleImputer(strategy='median'), StandardScaler()), numeric),
         ('cat', make_pipeline(SimpleImputer(strategy='most_frequent'), OneHotEncoder(handle_unknown='ignore', dtype=np.float32)), categorical)]
preprocessor = ColumnTransformer(parts, sparse_threshold=0)
Xtr = preprocessor.fit_transform(frame_x(train)).astype('float32')
Xva = preprocessor.transform(frame_x(val)).astype('float32')
Xte = preprocessor.transform(frame_x(test)).astype('float32')
ytr, yva, yte = [f['class'].to_numpy(dtype='float32') for f in (train, val, test)]
print('Kích thước sau tiền xử lý (fit chỉ trên train):', Xtr.shape, Xva.shape, Xte.shape, '| Xtr MB:', round(Xtr.nbytes / 1e6))
'''

TRAINING = r'''
# Cùng tập train/validation cho tất cả ứng viên. Ba seed chỉ thay đổi khởi tạo,
# không thay thế việc đánh giá trên nhiều phép chia dữ liệu độc lập.
from copy import deepcopy
MLP_TRAIN_MAX = __MLP_MAX__  # None = MLP học trên toàn bộ train; số nguyên = mẫu con phân tầng (LR/HGB luôn dùng toàn bộ train)
TRAINING_SECONDS = {}
candidates = {
    'dummy': DummyClassifier(strategy='prior'),
    'logistic_regression': LogisticRegression(max_iter=1000, class_weight='balanced', random_state=SEED),
    'hist_gradient_boosting': HistGradientBoostingClassifier(max_iter=100 if not SMOKE else 5, max_leaf_nodes=15, class_weight='balanced', random_state=SEED),
}
for name, estimator in candidates.items():
    t0 = time.perf_counter(); print('Training', name, flush=True); estimator.fit(Xtr, ytr)
    TRAINING_SECONDS[name] = round(time.perf_counter() - t0, 1); print(f'  {name}: {TRAINING_SECONDS[name]} s', flush=True)

seeds = [42] if SMOKE else [42, 43, 44]
max_epochs = 2 if SMOKE else 200
min_epochs = 1 if SMOKE else 40
patience_limit = 2 if SMOKE else 25
batch_size = 4096
if MLP_TRAIN_MAX and len(ytr) > MLP_TRAIN_MAX:
    mlp_idx = np.sort(train_test_split(np.arange(len(ytr)), train_size=MLP_TRAIN_MAX, stratify=ytr, random_state=SEED)[0])
else:
    mlp_idx = np.arange(len(ytr))
xt = torch.from_numpy(Xtr[mlp_idx]) if len(mlp_idx) < len(ytr) else torch.from_numpy(Xtr)
yt = torch.from_numpy(ytr[mlp_idx]) if len(mlp_idx) < len(ytr) else torch.from_numpy(ytr)
xv, yv = torch.from_numpy(Xva), torch.from_numpy(yva)
print('MLP học trên', len(yt), 'dòng train')
pos_weight = torch.tensor([(len(yt) - float(yt.sum())) / float(yt.sum())], dtype=torch.float32)
loss_fn = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
runs = []
for run_seed in seeds:
    t0 = time.perf_counter()
    torch.manual_seed(run_seed); random.seed(run_seed); np.random.seed(run_seed)
    model = Net(Xtr.shape[1]); optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    generator = torch.Generator().manual_seed(run_seed)
    best_loss = float('inf'); best_state = None; best_epoch = 0; patience = 0; history = []; updates = 0
    for epoch in range(1, max_epochs + 1):
        model.train(); total_loss = 0.0
        order = torch.randperm(len(yt), generator=generator)  # cắt lô trực tiếp từ tensor, nhanh hơn DataLoader nhiều lần
        for start in range(0, len(order), batch_size):
            ix = order[start:start + batch_size]
            x, y = xt[ix], yt[ix]
            optimizer.zero_grad(); loss = loss_fn(model(x), y); loss.backward(); optimizer.step()
            total_loss += float(loss.detach()) * len(y); updates += 1
        model.eval()
        with torch.no_grad(): val_loss = float(loss_fn(model(xv), yv))
        history.append({'epoch': epoch, 'train_loss': total_loss / len(yt), 'val_loss': val_loss})
        if val_loss < best_loss - 1e-4:
            best_loss = val_loss; best_epoch = epoch; best_state = deepcopy(model.state_dict()); patience = 0
        else: patience += 1
        if epoch >= min_epochs and patience >= patience_limit: break
        if epoch % 10 == 0: print(f'  seed {run_seed} epoch {epoch}: val_loss={val_loss:.4f}, {time.perf_counter() - t0:.0f} s', flush=True)
    model.load_state_dict(best_state); model.eval()
    with torch.no_grad(): valid_scores = torch.sigmoid(model(xv)).numpy()
    run = {'seed': run_seed, 'model': model, 'best_epoch': best_epoch, 'epochs_run': len(history),
           'updates': updates, 'stopped_early': len(history) < max_epochs, 'history': history,
           'val_scores': valid_scores, 'val_auc': float(roc_auc_score(yva, valid_scores))}
    runs.append(run)
    TRAINING_SECONDS[f'neural_seed_{run_seed}'] = round(time.perf_counter() - t0, 1)
    print(f"seed={run_seed}: epochs={len(history)}, best={best_epoch}, updates={updates}, val AUC={run['val_auc']:.4f}, early_stop={run['stopped_early']}, {TRAINING_SECONDS[f'neural_seed_{run_seed}']} s", flush=True)
EXTRA_REPORT['training_seconds'] = TRAINING_SECONDS
EXTRA_REPORT['mlp_train_rows'] = int(len(yt)); EXTRA_REPORT['mlp_train_subsampled'] = bool(len(yt) < len(ytr))

fig, axes = plt.subplots(1, 2, figsize=(12, 4))
for run in runs:
    curve = pd.DataFrame(run['history'])
    axes[0].plot(curve.epoch, curve.train_loss, label=f"seed {run['seed']}")
    axes[1].plot(curve.epoch, curve.val_loss, label=f"seed {run['seed']} — tốt nhất {run['best_epoch']}")
for ax, title in zip(axes, ['Train loss (batch)', 'Validation loss (2022)']): ax.set_title(title); ax.set_xlabel('Epoch'); ax.set_ylabel('Weighted BCE'); ax.legend()
plt.tight_layout(); plt.show()
print('Dao động validation AUC giữa các seed:', [round(r['val_auc'], 4) for r in runs])
'''

PER_YEAR = r'''
# Hiệu năng của mô hình ĐÃ CHỌN theo từng năm (ngưỡng đã chọn trên validation 2022).
def selected_scores(X):
    if selected.startswith('neural_seed_'):
        out = []
        with torch.no_grad():
            for s in range(0, len(X), 200000): out.append(torch.sigmoid(best_run['model'](torch.from_numpy(X[s:s + 200000]))).numpy())
        return np.concatenate(out)
    return candidates[selected].predict_proba(X)[:, 1]
train_scores_all = selected_scores(Xtr)
rows = []
for year in TRAIN_YEARS:
    mask = (train.year == year).to_numpy()
    rows.append({'năm': year, 'vai trò': 'train (trong mẫu, lạc quan)', 'n': int(mask.sum()), 'tỷ lệ dương': float(ytr[mask].mean()), **threshold_scores(ytr[mask], train_scores_all[mask], selected_threshold)})
rows.append({'năm': VAL_YEAR, 'vai trò': 'validation', 'n': len(yva), 'tỷ lệ dương': float(yva.mean()), **threshold_scores(yva, val_scores[selected], selected_threshold)})
rows.append({'năm': TEST_YEAR, 'vai trò': 'test', 'n': len(yte), 'tỷ lệ dương': float(yte.mean()), **threshold_scores(yte, test_scores, selected_threshold)})
per_year = pd.DataFrame(rows)
print(per_year.round(4).to_string(index=False))
del train_scores_all
fig, ax = plt.subplots(figsize=(7, 3.5))
ax.plot(per_year['năm'], per_year['roc_auc'], marker='o'); ax.set(title=f'ROC-AUC theo năm — {selected}', xlabel='Năm', ylabel='ROC-AUC'); plt.tight_layout(); plt.show()
EXTRA_REPORT['per_year_metrics_selected_model'] = per_year.to_dict(orient='records')
'''

ABLATION = r'''
# Thêm năm cũ vào train có giúp không? HistGradientBoosting cùng siêu tham số, chỉ đổi cửa sổ năm train (kết thúc 2021),
# đánh giá trên validation 2022 và test 2023 (cùng ngưỡng 0,5 chỉ để tham khảo; so sánh bằng ROC-AUC/PR-AUC).
# Đây là phân tích chẩn đoán trên test đã được xem, KHÔNG dùng để chọn mô hình.
from sklearn.base import clone
windows = {'2021': [2021], '2020–2021': [2020, 2021], '2018–2021': list(range(2018, 2022)), '2015–2021': TRAIN_YEARS}
ablation_rows = []
for label, years in windows.items():
    if SMOKE and len(years) > 2: continue
    mask = train.year.isin(years).to_numpy(); t0 = time.perf_counter()
    prep = clone(preprocessor).fit(frame_x(train[mask]))
    est = HistGradientBoostingClassifier(max_iter=100 if not SMOKE else 5, max_leaf_nodes=15, class_weight='balanced', random_state=SEED)
    est.fit(prep.transform(frame_x(train[mask])).astype('float32'), ytr[mask])
    sv = est.predict_proba(prep.transform(frame_x(val)).astype('float32'))[:, 1]
    st = est.predict_proba(prep.transform(frame_x(test)).astype('float32'))[:, 1]
    ablation_rows.append({'cửa sổ train': label, 'n train': int(mask.sum()), 'val 2022 ROC-AUC': roc_auc_score(yva, sv), 'test 2023 ROC-AUC': roc_auc_score(yte, st),
                          'test 2023 PR-AUC': average_precision_score(yte, st), 'giây': round(time.perf_counter() - t0, 1)})
    print(ablation_rows[-1], flush=True)
ablation = pd.DataFrame(ablation_rows); print(ablation.round(4).to_string(index=False))
EXTRA_REPORT['train_window_ablation_hgb'] = ablation.to_dict(orient='records')
'''

COMPARE = r'''
# So sánh với notebook 07 trên CÙNG tập test 2023.
BASELINE_REPORT = ROOT/'artifacts/notebook_runs/brfss20/20261112T073448_850428Z/report.json'
base = json.loads(BASELINE_REPORT.read_text(encoding='utf-8'))
if not SMOKE:
    assert base['sizes']['test'] == len(test), f"Test khác nhau: 07={base['sizes']['test']}, 11={len(test)}"
    assert base['class_counts']['test'] == {str(k): int(v) for k, v in test['class'].value_counts().items()}, 'Phân bố nhãn test khác notebook 07'
t07 = base['test_selected_only']; ci07 = base['test_auc_bootstrap_stratified_95']
comparison = pd.DataFrame([
    {'notebook': '07 (2021–22 -> 2023)', 'train': base['sizes']['train'], 'validation': base['sizes']['validation'], 'cách chia val': 'ngẫu nhiên 20% của 2021–22', 'mô hình': base['selected_model'],
     'ROC-AUC': t07['roc_auc'], 'CI thấp': ci07[0], 'CI cao': ci07[1], 'PR-AUC': t07['pr_auc'], 'precision': t07['precision'], 'recall': t07['recall'], 'f1': t07['f1'], 'ngưỡng': base['selected_threshold']},
    {'notebook': '11 (2015–21 -> 2023)', 'train': len(train), 'validation': len(val), 'cách chia val': 'năm 2022', 'mô hình': selected,
     'ROC-AUC': test_metrics['roc_auc'], 'CI thấp': auc_ci[0], 'CI cao': auc_ci[1], 'PR-AUC': test_metrics['pr_auc'], 'precision': test_metrics['precision'], 'recall': test_metrics['recall'], 'f1': test_metrics['f1'], 'ngưỡng': selected_threshold}])
print(comparison.round(4).T.to_string())
print('\nThời gian train 07 (không ghi trong report; xem output notebook 07). Thời gian train 11 (giây):', TRAINING_SECONDS)
print('Khác biệt ROC-AUC (11 - 07):', round(test_metrics['roc_auc'] - t07['roc_auc'], 4))
EXTRA_REPORT['comparison_with_notebook_07'] = comparison.to_dict(orient='records')
EXTRA_REPORT['notebook_wall_seconds_before_save'] = round(time.perf_counter() - NOTEBOOK_T0, 1)
'''


def main(mlp_max=None):
    load = (LOAD.replace('__FEATURES__', repr(FEATURES)).replace('__DESC__', repr({k: v for k, v in DESC.items() if k in FEATURES}))
            .replace('__SPANS__', repr(SPANS)).replace('__DROPPED__', repr(DROPPED)).replace('__CODEBOOKS__', repr({str(k): v for k, v in CODEBOOKS.items()})))
    clean = CLEAN.replace('__CODES__', repr({k: v for k, v in CODES.items() if k in FEATURES}))
    extra = [md('## 9c. Hiệu năng theo từng năm\nMô hình đã chọn, ngưỡng cố định từ validation. Các năm train là trong mẫu nên lạc quan; chỉ validation 2022 và test 2023 là ngoài mẫu.'), code(PER_YEAR),
             md('## 9d. Thêm năm cũ vào train có giúp không?\nHistGradientBoosting cùng siêu tham số, chỉ đổi số năm train. Phân tích chẩn đoán, không dùng để chọn mô hình.'), code(ABLATION),
             md('## 9e. So sánh với notebook 07\nCùng test 2023 (cùng số dòng và số ca dương). Khác nhau: dữ liệu train, cách chia validation, và biến thu nhập (5 mức thay vì 7).'), code(COMPARE)]
    out = '11_BRFSS_2015_2023_Lon.ipynb'
    build('02_BRFSS_Khao_Sat.ipynb', out, INTRO,
          ('brfss_2015_2023', 'MLP', 'BRFSS 2015–2023: train 2015–2021, validation 2022, test 2023; 20 biến hài hoà qua 9 năm; nhãn tự khai từng được báo mắc ĐTĐ; không dùng survey weight.'),
          load, clean, extra)
    nb = json.loads((HERE / out).read_text(encoding='utf-8'))
    for i, c in enumerate(nb['cells']):
        s = ''.join(c['source']) if c['cell_type'] == 'code' else ''
        if s.startswith('def frame_x(frame):'): nb['cells'][i]['source'] = PREPROC.strip('\n')
        elif s.startswith('# Cùng tập train/validation cho tất cả ứng viên'): nb['cells'][i]['source'] = TRAINING.replace('__MLP_MAX__', repr(mlp_max)).strip('\n')
    (HERE / out).write_text(json.dumps(nb, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    print('patched', out)


if __name__ == '__main__':
    import sys
    main(int(sys.argv[1]) if len(sys.argv) > 1 else None)
