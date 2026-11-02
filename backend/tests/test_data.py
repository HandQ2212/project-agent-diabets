import pandas as pd
import pytest
from ml.train import SYMPTOMS, symptom_data, metrics

def test_symptom_schema_and_labels(tmp_path):
    records = [{**{key: ('32' if key == 'age' else 'Male' if key == 'gender' else 'No') for key in SYMPTOMS}, 'class': label} for label in ['Positive', 'Negative']]
    path = tmp_path/'samples.csv'; pd.DataFrame(records).to_csv(path, index=False)
    df = symptom_data(path)
    assert df['class'].tolist() == [1, 0]
    assert df['age'].tolist() == [32, 32]
    assert df['gender'].tolist() == ['male', 'male']

def test_metrics_single_class_and_confusion_matrix():
    result = metrics([0, 0], [0.1, 0.8])
    assert result['roc_auc'] is None
    assert result['confusion_matrix'] == [[1, 1], [0, 0]]

def test_symptom_columns_required(tmp_path):
    path = tmp_path/'invalid.csv'; path.write_text('age,class\n30,Positive\n')
    with pytest.raises(ValueError, match='columns missing'): symptom_data(path)
