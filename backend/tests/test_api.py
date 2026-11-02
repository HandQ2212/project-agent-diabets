from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_and_invalid_prediction():
    assert client.get('/api/health').status_code == 200
    response = client.post('/api/predict', json={'kind': 'symptoms', 'features': {}})
    assert response.status_code == 422

def test_rule_blocks_dosage_without_external_services():
    response = client.post('/api/chat', json={'question': 'Tôi nên tăng liều insulin như thế nào?'})
    assert response.status_code == 200
    assert response.json()['sources'] == []
    assert 'không thể' in response.json()['answer']
    assert 'Rule Agent' in response.json()['trace']

def test_missing_model_is_explicit(monkeypatch, tmp_path):
    import backend.app.main as module
    from ml.train import SYMPTOMS
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    features = {key: ('30' if key == 'age' else 'male' if key == 'gender' else 'no') for key in SYMPTOMS}
    response = client.post('/api/predict', json={'kind': 'symptoms', 'features': features})
    assert response.status_code == 503
