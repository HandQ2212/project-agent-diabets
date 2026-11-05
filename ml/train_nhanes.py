"""Research-only NHANES experiment: CNN on measurements, independent survey label.

Download public CDC XPT files, train on 2015–16 and evaluate on 2017–18.
Not a diagnostic or prospective risk model.
"""
import hashlib
import json
import random
import urllib.request
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, average_precision_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from torch import nn

FEATURES = ['RIDAGEYR', 'BMXBMI', 'LBXGLU', 'LBXGH']
FILES = {'DEMO': ['SEQN', 'RIDAGEYR'], 'DIQ': ['SEQN', 'DIQ010'],
         'BMX': ['SEQN', 'BMXBMI'], 'GLU': ['SEQN', 'LBXGLU'], 'GHB': ['SEQN', 'LBXGH']}
DATA = Path('data/raw/nhanes')
OUTPUT = Path('artifacts/nhanes_research')


class ClinicalCNN(nn.Module):
    """Assignment 04-style 1D CNN; the feature order is a modeling choice."""
    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(nn.Conv1d(1, 16, 3, padding=1), nn.ReLU(),
                                      nn.Conv1d(16, 32, 3, padding=1), nn.ReLU(), nn.MaxPool1d(2))
        self.classifier = nn.Sequential(nn.Flatten(), nn.Linear(64, 32), nn.ReLU(),
                                        nn.Dropout(0.2), nn.Linear(32, 1))

    def forward(self, x):
        return self.classifier(self.features(x.unsqueeze(1))).squeeze(1)


def load_cycle(year, suffix):
    frames, hashes = [], {}
    DATA.mkdir(parents=True, exist_ok=True)
    for name, columns in FILES.items():
        file = DATA / f'{name}_{suffix}.xpt'
        url = f'https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/{year}/DataFiles/{name}_{suffix}.xpt'
        if not file.exists():
            with urllib.request.urlopen(url, timeout=90) as response:
                payload = response.read()
            if not payload.startswith(b'HEADER RECORD'): raise ValueError(f'Invalid XPT: {url}')
            file.write_bytes(payload)
        hashes[file.name] = hashlib.sha256(file.read_bytes()).hexdigest()
        frame = pd.read_sas(file, format='xport')[columns]
        if frame.SEQN.duplicated().any(): raise ValueError(f'Duplicate participants in {file}')
        frames.append(frame)
    data = frames[0]
    for frame in frames[1:]:
        data = data.merge(frame, on='SEQN', validate='one_to_one')
    eligible = data[(data.RIDAGEYR >= 18) & data.DIQ010.isin([1, 2])]
    complete = eligible.dropna(subset=FEATURES).copy()
    complete['target'] = (complete.DIQ010 == 1).astype(int)
    return complete, {'merged': len(data), 'eligible': len(eligible), 'complete': len(complete),
                      'positive': int(complete.target.sum()), 'sha256': hashes}


def metrics(y, scores):
    pred = scores >= 0.5
    return {'roc_auc': roc_auc_score(y, scores), 'average_precision': average_precision_score(y, scores),
            'accuracy': accuracy_score(y, pred), 'precision': precision_score(y, pred, zero_division=0),
            'recall': recall_score(y, pred, zero_division=0), 'f1': f1_score(y, pred, zero_division=0),
            'confusion_matrix': confusion_matrix(y, pred, labels=[0, 1]).tolist()}


def main():
    random.seed(42); np.random.seed(42); torch.manual_seed(42); torch.set_num_threads(1)
    older, older_info = load_cycle(2015, 'I')
    newer, newer_info = load_cycle(2017, 'J')
    train, val = train_test_split(older, test_size=0.2, stratify=older.target, random_state=42)
    scaler = StandardScaler().fit(train[FEATURES])
    xt = torch.tensor(scaler.transform(train[FEATURES]), dtype=torch.float32)
    yt = torch.tensor(train.target.to_numpy(), dtype=torch.float32)
    xv = torch.tensor(scaler.transform(val[FEATURES]), dtype=torch.float32)
    yv = torch.tensor(val.target.to_numpy(), dtype=torch.float32)
    test_x = scaler.transform(newer[FEATURES])
    model = ClinicalCNN()
    opt = torch.optim.Adam(model.parameters(), lr=0.001)
    loss_fn = nn.BCEWithLogitsLoss(pos_weight=torch.tensor([(len(yt)-yt.sum())/yt.sum()]))
    loader = torch.utils.data.DataLoader(torch.utils.data.TensorDataset(xt, yt), batch_size=64, shuffle=True)
    best_loss, best_state, best_epoch, patience = float('inf'), None, 0, 0
    for epoch in range(1, 101):
        model.train()
        for x, y in loader:
            opt.zero_grad(); loss = loss_fn(model(x), y); loss.backward(); opt.step()
        model.eval()
        with torch.no_grad(): loss = loss_fn(model(xv), yv).item()
        if loss < best_loss - 1e-5:
            best_loss, best_epoch, patience = loss, epoch, 0
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
        else:
            patience += 1
            if patience >= 10: break
    model.load_state_dict(best_state); model.eval()
    with torch.no_grad(): scores = torch.sigmoid(model(torch.tensor(test_x, dtype=torch.float32))).numpy()
    baseline = LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42).fit(scaler.transform(train[FEATURES]), train.target)
    report = {'task': 'Classify self-reported prior diagnosis, not predict onset or diagnose diabetes',
              'features': FEATURES, 'train_cycle': older_info, 'test_cycle': newer_info,
              'train_n': len(train), 'validation_n': len(val), 'seed': 42, 'best_epoch': best_epoch,
              'cnn': metrics(newer.target, scores), 'logistic_regression': metrics(newer.target, baseline.predict_proba(test_x)[:, 1]),
              'limitations': ['Retrospective self-report; disease treatment can affect measurements',
                              'Complete cases from fasting subsample; unweighted survey; not population representative',
                              'HbA1c and glucose are diagnostic measurements; possible overlap with historical diagnosis',
                              'CNN feature order is arbitrary; no clinical or external validation for Vietnam',
                              'Not for individual screening, clinical decisions, or diagnosis']}
    OUTPUT.mkdir(parents=True, exist_ok=True)
    torch.save({'state_dict': best_state, 'features': FEATURES}, OUTPUT / 'model.pt')
    joblib.dump(scaler, OUTPUT / 'scaler.joblib')
    (OUTPUT / 'report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == '__main__': main()
