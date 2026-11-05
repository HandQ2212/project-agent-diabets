"""Reproduce an assignment-style experiment without feeding its label into X."""
import json
import random
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from ml.train_nhanes import ClinicalCNN, metrics


def main():
    random.seed(42); np.random.seed(42); torch.manual_seed(42); torch.set_num_threads(1)
    path = Path('data/raw/assignment02_diabetes.csv')
    data = pd.read_csv(path)
    data['bmi'] = data['weight'] * 0.45359237 / (data['height'] * 0.0254) ** 2
    columns = ['age', 'bmi', 'stab.glu', 'chol']
    data = data.replace([np.inf, -np.inf], np.nan).dropna(subset=columns + ['glyhb']).copy()
    data = data[(data.height > 0) & (data.weight > 0) & (data['stab.glu'] > 0) & (data.chol > 0)]
    # Replicates assignment 07's synthetic threshold exactly; not a diagnosis.
    data['target'] = (data.glyhb > 6.5).astype(int)
    trainval, test = train_test_split(data, test_size=0.2, stratify=data.target, random_state=42)
    train, val = train_test_split(trainval, test_size=0.2, stratify=trainval.target, random_state=42)
    scaler = StandardScaler().fit(train[columns])
    xt = torch.tensor(scaler.transform(train[columns]), dtype=torch.float32)
    yt = torch.tensor(train.target.to_numpy(), dtype=torch.float32)
    xv = torch.tensor(scaler.transform(val[columns]), dtype=torch.float32)
    yv = torch.tensor(val.target.to_numpy(), dtype=torch.float32)
    model = ClinicalCNN(); opt = torch.optim.Adam(model.parameters(), lr=0.001)
    loss_fn = torch.nn.BCEWithLogitsLoss(pos_weight=torch.tensor([(len(yt)-yt.sum())/yt.sum()]))
    best, state, epoch_best, patience = float('inf'), None, 0, 0
    for epoch in range(1, 201):
        model.train(); opt.zero_grad(); loss_fn(model(xt), yt).backward(); opt.step()
        model.eval()
        with torch.no_grad(): loss = loss_fn(model(xv), yv).item()
        if loss < best - 1e-5:
            best, state, epoch_best, patience = loss, {k: v.clone() for k, v in model.state_dict().items()}, epoch, 0
        else:
            patience += 1
            if patience >= 15: break
    model.load_state_dict(state); model.eval()
    xx = scaler.transform(test[columns])
    with torch.no_grad(): scores = torch.sigmoid(model(torch.tensor(xx, dtype=torch.float32))).numpy()
    baseline = LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42).fit(scaler.transform(train[columns]), train.target)
    report = {'task': 'Predict synthetic label glyhb > 6.5, not diabetes diagnosis', 'features': columns,
              'excluded': ['glyhb', 'id', 'Outcome'], 'complete_rows': len(data),
              'train_n': len(train), 'validation_n': len(val), 'test_n': len(test),
              'seed': 42, 'best_epoch': epoch_best, 'cnn': metrics(test.target, scores),
              'logistic_regression': metrics(test.target, baseline.predict_proba(xx)[:, 1]),
              'limitations': ['Synthetic target, small test set, source and units require independent verification',
                              'No independent diagnosis label, no clinical validation, not a diagnostic model']}
    out = Path('artifacts/assignment02_research'); out.mkdir(parents=True, exist_ok=True)
    (out / 'report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == '__main__': main()
