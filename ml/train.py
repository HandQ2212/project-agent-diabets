"""Train reproducible educational classifiers; see docs/DATA.md for cohort definitions."""
import argparse
import json
import logging
import random
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import torch
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, brier_score_loss
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from torch import nn

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

SYMPTOMS = [
    'age', 'gender', 'polyuria', 'polydipsia', 'sudden_weight_loss', 'weakness',
    'polyphagia', 'genital_thrush', 'visual_blurring', 'itching', 'irritability',
    'delayed_healing', 'partial_paresis', 'muscle_stiffness', 'alopecia', 'obesity'
]
BRFSS = ['_AGEG5YR', '_BMI5', 'SEXVAR', '_SMOKER3', '_TOTINDA']
CODES = {
    '_AGEG5YR': list(range(1, 14)),
    'SEXVAR': [1, 2],
    '_SMOKER3': [1, 2, 3, 4],
    '_TOTINDA': [1, 2]
}

class Network(nn.Module):
    def __init__(self, n: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(n, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )
    def forward(self, x):
        return self.net(x).squeeze(-1)

def symptom_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]
    missing = set(SYMPTOMS + ['class']) - set(df.columns)
    if missing:
        raise ValueError(f'UCI columns missing: {sorted(missing)}')
    df = df[SYMPTOMS + ['class']].copy()
    df['class'] = df['class'].astype(str).str.strip().str.lower().map({'positive': 1, 'negative': 0})
    df['age'] = pd.to_numeric(df['age'], errors='coerce')
    for c in SYMPTOMS[1:]:
        df[c] = df[c].astype('string').str.strip().str.lower()
    return df.dropna(subset=['class'])

def brfss_data(path: str, year: int) -> pd.DataFrame:
    import pyreadstat
    required = set(BRFSS + ['DIABETE4'])
    df, _ = pyreadstat.read_xport(path, usecols=sorted(required))
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f'{year}: columns missing: {sorted(missing)}; inspect CDC codebook before changing the feature contract')
    df = df[list(BRFSS) + ['DIABETE4']].copy()
    # Exclude gestational diabetes (2), prediabetes (4) and unknown (7, 9, blank) from binary outcome
    df = df[df.DIABETE4.isin([1, 3])].copy()
    df['class'] = df.DIABETE4.map({1: 1, 3: 0})
    for col, valid in CODES.items():
        df[col] = pd.to_numeric(df[col], errors='coerce').where(df[col].isin(valid))
    df['_BMI5'] = pd.to_numeric(df['_BMI5'], errors='coerce') / 100
    df['_BMI5'] = df['_BMI5'].where(df['_BMI5'].between(10, 100))
    return df.drop(columns='DIABETE4')

def metrics(y, p):
    y = np.asarray(y)
    p = np.asarray(p)
    out = {
        'confusion_matrix': confusion_matrix(y, p >= 0.5, labels=[0, 1]).tolist(),
        'classification_report': classification_report(y, p >= 0.5, output_dict=True, zero_division=0)
    }
    out['roc_auc'] = float(roc_auc_score(y, p)) if len(np.unique(y)) == 2 else None
    out['brier_score'] = float(brier_score_loss(y, p))
    
    # Threshold sweep evaluation
    thresholds = [0.3, 0.4, 0.5, 0.6, 0.7]
    sweep = {}
    for th in thresholds:
        pred_th = (p >= th).astype(int)
        rep = classification_report(y, pred_th, output_dict=True, zero_division=0)
        cm = confusion_matrix(y, pred_th, labels=[0, 1]).tolist()
        sweep[str(th)] = {
            'precision_pos': rep['1']['precision'],
            'recall_pos': rep['1']['recall'],
            'f1_pos': rep['1']['f1-score'],
            'accuracy': rep['accuracy'],
            'confusion_matrix': cm
        }
    out['threshold_sweep'] = sweep
    return out

def subgroup_metrics(test_df: pd.DataFrame, y_true: np.ndarray, y_prob: np.ndarray, kind: str) -> dict:
    subgroups = {}
    if kind == 'symptoms':
        # Subgroup by gender
        for g in ['male', 'female']:
            mask = (test_df['gender'] == g).fillna(False).to_numpy(dtype=bool)
            if mask.sum() >= 5 and len(np.unique(y_true[mask])) == 2:
                subgroups[f"gender_{g}"] = {
                    'count': int(mask.sum()),
                    'positive_rate': float(np.mean(y_true[mask])),
                    'roc_auc': float(roc_auc_score(y_true[mask], y_prob[mask])),
                    'brier_score': float(brier_score_loss(y_true[mask], y_prob[mask]))
                }
        # Subgroup by age
        mask_young = (test_df['age'] < 50).fillna(False).to_numpy(dtype=bool)
        mask_old = (test_df['age'] >= 50).fillna(False).to_numpy(dtype=bool)
        for label, m in [('age_under_50', mask_young), ('age_50_plus', mask_old)]:
            if m.sum() >= 5 and len(np.unique(y_true[m])) == 2:
                subgroups[label] = {
                    'count': int(m.sum()),
                    'positive_rate': float(np.mean(y_true[m])),
                    'roc_auc': float(roc_auc_score(y_true[m], y_prob[m])),
                    'brier_score': float(brier_score_loss(y_true[m], y_prob[m]))
                }
    else:
        # BRFSS Subgroups: Gender (SEXVAR: 1=Male, 2=Female)
        sex_col = pd.to_numeric(test_df['SEXVAR'], errors='coerce')
        for code, name in [(1, 'male'), (2, 'female')]:
            mask = (sex_col == code).fillna(False).to_numpy(dtype=bool)
            if mask.sum() >= 100:
                subgroups[f"sex_{name}"] = {
                    'count': int(mask.sum()),
                    'positive_rate': float(np.mean(y_true[mask])),
                    'roc_auc': float(roc_auc_score(y_true[mask], y_prob[mask])),
                    'brier_score': float(brier_score_loss(y_true[mask], y_prob[mask]))
                }
        # Age groups (18-39: 1-4, 40-59: 5-8, 60+: 9-13)
        age_num = pd.to_numeric(test_df['_AGEG5YR'], errors='coerce')
        for label, (low, high) in [('age_18_39', (1, 4)), ('age_40_59', (5, 8)), ('age_60_plus', (9, 13))]:
            mask = (age_num.between(low, high)).fillna(False).to_numpy(dtype=bool)
            if mask.sum() >= 100:
                subgroups[label] = {
                    'count': int(mask.sum()),
                    'positive_rate': float(np.mean(y_true[mask])),
                    'roc_auc': float(roc_auc_score(y_true[mask], y_prob[mask])),
                    'brier_score': float(brier_score_loss(y_true[mask], y_prob[mask]))
                }
        # Smoking status (1-2: current, 3: former, 4: never)
        smk_num = pd.to_numeric(test_df['_SMOKER3'], errors='coerce')
        for label, cond in [('smoker_current', smk_num.isin([1, 2])), ('smoker_former', smk_num == 3), ('smoker_never', smk_num == 4)]:
            mask = cond.fillna(False).to_numpy(dtype=bool)
            if mask.sum() >= 100:
                subgroups[label] = {
                    'count': int(mask.sum()),
                    'positive_rate': float(np.mean(y_true[mask])),
                    'roc_auc': float(roc_auc_score(y_true[mask], y_prob[mask])),
                    'brier_score': float(brier_score_loss(y_true[mask], y_prob[mask]))
                }
        # Physical activity (_TOTINDA: 1=active, 2=inactive)
        act_num = pd.to_numeric(test_df['_TOTINDA'], errors='coerce')
        for label, code in [('physically_active', 1), ('physically_inactive', 2)]:
            mask = (act_num == code).fillna(False).to_numpy(dtype=bool)
            if mask.sum() >= 100:
                subgroups[label] = {
                    'count': int(mask.sum()),
                    'positive_rate': float(np.mean(y_true[mask])),
                    'roc_auc': float(roc_auc_score(y_true[mask], y_prob[mask])),
                    'brier_score': float(brier_score_loss(y_true[mask], y_prob[mask]))
                }
    return subgroups

def train(kind: str, paths: list[str], output: str):
    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)

    log.info(f"Starting training pipeline for {kind.upper()}...")
    if kind == 'symptoms':
        df = symptom_data(paths[0])
        source_rows = len(df)
        conflicts = df.groupby(SYMPTOMS, dropna=False)['class'].transform('nunique') > 1
        conflict_rows = int(conflicts.sum())
        df = df.loc[~conflicts].drop_duplicates(subset=SYMPTOMS).copy()
        trainval, test = train_test_split(df, test_size=0.2, random_state=42, stratify=df['class'])
        numeric, categorical = ['age'], SYMPTOMS[1:]
        counts = {'source_rows': source_rows, 'conflicting_rows_removed': conflict_rows, 'unique_profiles': len(df)}
    else:
        years = [2021, 2022, 2023]
        frames = [brfss_data(p, y) for p, y in zip(paths, years)]
        trainval = pd.concat(frames[:2], ignore_index=True)
        test = frames[2]
        numeric, categorical = ['_BMI5'], [c for c in BRFSS if c != '_BMI5']
        for frame in frames:
            for col in categorical:
                frame[col] = frame[col].astype('Int64').astype('string')
        for col in categorical:
            trainval[col] = trainval[col].astype('Int64').astype('string')
        counts = {str(y): len(f) for y, f in zip(years, frames)}

    train_df, val = train_test_split(trainval, test_size=0.2, random_state=42, stratify=trainval['class'])
    features = numeric + categorical

    prep = ColumnTransformer(
        [
            ('num', make_pipeline(SimpleImputer(strategy='median'), StandardScaler()), numeric),
            ('cat', make_pipeline(SimpleImputer(strategy='most_frequent'), OneHotEncoder(handle_unknown='ignore')), categorical)
        ],
        sparse_threshold=0
    )

    def clean(frame):
        x = frame[features].copy()
        for c in categorical:
            x[c] = x[c].astype(object).where(x[c].notna(), np.nan)
        return x

    xtr = prep.fit_transform(clean(train_df)).astype('float32')
    xv = prep.transform(clean(val)).astype('float32')
    xt = prep.transform(clean(test)).astype('float32')

    ytr = train_df['class'].astype(int).to_numpy()
    yv = val['class'].astype(int).to_numpy()
    yt = test['class'].astype(int).to_numpy()

    # Train Baseline Logistic Regression
    baseline = LogisticRegression(max_iter=1000, class_weight='balanced', random_state=42).fit(xtr, ytr)
    p_baseline = baseline.predict_proba(xt)[:, 1]

    # Train PyTorch Neural Network MLP
    model = Network(xtr.shape[1])
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    pos_weight = torch.tensor([(len(ytr) - ytr.sum()) / max(ytr.sum(), 1)], dtype=torch.float32)
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)

    loader = torch.utils.data.DataLoader(
        torch.utils.data.TensorDataset(torch.from_numpy(xtr), torch.tensor(ytr, dtype=torch.float32)),
        batch_size=256,
        shuffle=True
    )

    best_loss = float('inf')
    best = None
    patience = 0

    for epoch in range(60):
        model.train()
        for xb, yb in loader:
            optimizer.zero_grad()
            loss = criterion(model(xb), yb)
            loss.backward()
            optimizer.step()
        model.eval()
        with torch.no_grad():
            val_loss = criterion(model(torch.from_numpy(xv)), torch.tensor(yv, dtype=torch.float32)).item()
        if val_loss < best_loss - 1e-4:
            best_loss = val_loss
            best = {k: v.detach().clone() for k, v in model.state_dict().items()}
            patience = 0
        else:
            patience += 1
            if patience >= 7:
                break

    model.load_state_dict(best)
    model.eval()
    with torch.no_grad():
        p_nn = torch.sigmoid(model(torch.from_numpy(xt))).numpy()

    out = Path(output) / kind
    out.mkdir(parents=True, exist_ok=True)
    joblib.dump(prep, out / 'preprocessor.joblib')
    torch.save({'input_size': xtr.shape[1], 'state_dict': model.state_dict()}, out / 'model.pt')
    joblib.dump(baseline, out / 'baseline.joblib')

    subgroup_res = subgroup_metrics(test, yt, p_nn, kind)

    report = {
        'cohort_counts': counts,
        'train': len(train_df),
        'validation': len(val),
        'test': len(test),
        'test_positive_fraction': float(np.mean(yt)),
        'features': features,
        'neural_network': metrics(yt, p_nn),
        'logistic_regression': metrics(yt, p_baseline),
        'subgroup_analysis': subgroup_res,
        'limitations': (
            'Educational use only. BRFSS is self-reported, cross-sectional and survey weights '
            'are not used in training or these metrics. Not calibrated for medical diagnosis or Vietnamese population. '
            'UCI is small (251 unique profiles) and from a single clinic in Sylhet, Bangladesh.'
        )
    }

    (out / 'report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    log.info(f"Report saved to {out / 'report.json'}")
    print(json.dumps({'output': str(out), 'counts': counts, 'test': len(test)}, indent=2))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('kind', choices=['symptoms', 'brfss'])
    parser.add_argument('paths', nargs='+')
    parser.add_argument('--output', default='artifacts')
    args = parser.parse_args()
    if len(args.paths) != (1 if args.kind == 'symptoms' else 3):
        parser.error('Provide UCI CSV, or BRFSS XPT files in 2021 2022 2023 order')
    train(args.kind, args.paths, args.output)
