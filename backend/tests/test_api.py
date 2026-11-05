from fastapi.testclient import TestClient
import json
import pytest
from backend.app.main import app

client = TestClient(app)

def test_nhanes15_uses_selected_model_and_threshold(monkeypatch, tmp_path):
    import json
    import joblib
    import pandas as pd
    import torch
    from sklearn.preprocessing import StandardScaler
    from backend.app import main, nhanes15
    monkeypatch.setattr(main, 'ROOT', tmp_path)
    folder = tmp_path / 'nhanes15_web'
    folder.mkdir()
    values = [45, 1, 25, 85, 120, 75, 100, 5.5, 180, 50, 120, 22, 0.9, 70, 170]
    features = dict(zip(nhanes15.FEATURES, values))
    joblib.dump(StandardScaler().fit(pd.DataFrame([features], columns=nhanes15.FEATURES)), folder / 'preprocessor.joblib')
    torch.save({'state_dict': nhanes15.NotebookCNN(15).state_dict(), 'architecture': 'CNN', 'input_size': 15}, folder / 'neural_seed_42.pt')
    (folder / 'report.json').write_text(json.dumps({'selected_model': 'neural_seed_42', 'features': nhanes15.FEATURES, 'selected_threshold': 0.8}))
    response = client.post('/api/predict', json={'kind': 'nhanes15_research', 'features': features})
    assert response.status_code == 200
    assert response.json()['threshold'] == 0.8
    assert response.json()['classification'] == int(response.json()['score'] >= 0.8)
    assert 'không dùng để sàng lọc' in response.json()['meaning']
    features['RIAGENDR'] = 1.5
    assert client.post('/api/predict', json={'kind': 'nhanes15_research', 'features': features}).status_code == 422
    features['RIAGENDR'] = 1
    report = json.loads((folder / 'report.json').read_text())
    report['features'].reverse()
    (folder / 'report.json').write_text(json.dumps(report))
    assert client.post('/api/predict', json={'kind': 'nhanes15_research', 'features': features}).status_code == 503

def test_nhanes_research_prediction_and_validation(monkeypatch, tmp_path):
    import joblib
    import pandas as pd
    import torch
    from sklearn.preprocessing import StandardScaler
    from backend.app import main
    from ml.train_nhanes import ClinicalCNN, FEATURES
    monkeypatch.setattr(main, 'ROOT', tmp_path)
    folder = tmp_path / 'nhanes_research'
    folder.mkdir()
    features = {'RIDAGEYR': 45, 'BMXBMI': 25, 'LBXGLU': 100, 'LBXGH': 5.5}
    joblib.dump(StandardScaler().fit(pd.DataFrame([features], columns=FEATURES)), folder / 'scaler.joblib')
    torch.save({'state_dict': ClinicalCNN().state_dict()}, folder / 'model.pt')
    response = client.post('/api/predict', json={'kind': 'nhanes_research', 'features': features})
    assert response.status_code == 200
    assert 0 <= response.json()['score'] <= 1
    assert 'không dùng để sàng lọc' in response.json()['meaning']
    assert 'CNN 1D' in ' '.join(response.json()['trace'])
    features['LBXGLU'] = 9999
    assert client.post('/api/predict', json={'kind': 'nhanes_research', 'features': features}).status_code == 422

@pytest.mark.parametrize('question,expected', [
    ('hello', 'Xin chào'), ('Hi!', 'Xin chào'), ('Cảm ơn bạn', 'Không có gì'),
    ('Giúp tôi trả lời Claude là gì?', 'Anthropic'),
])
@pytest.mark.parametrize('path', ['/api/chat', '/api/chat/stream'])
def test_conversation_does_not_search_knowledge(monkeypatch, path, question, expected):
    from backend.app import main
    monkeypatch.setattr(main.rag, 'retrieve', lambda *a, **k: (_ for _ in ()).throw(AssertionError('must not retrieve')))
    response = client.post(path, json={'question': question, 'history': [{'role': 'user', 'content': 'Tiểu đường là gì?'}]})
    assert response.status_code == 200
    if path.endswith('/stream'):
        events = [json.loads(line) for line in response.text.splitlines()]
        assert expected in ''.join(e.get('text', '') for e in events)
        result = events[-1]
    else:
        result = response.json()
        assert expected in result['answer']
    assert result['sources'] == []
    assert 'Conversation Agent' in result['trace']

@pytest.mark.parametrize('path', ['/api/chat', '/api/chat/stream'])
def test_greeting_with_emergency_still_uses_safety_rules(path):
    response = client.post(path, json={'question': 'Hello, người nhà tôi bất tỉnh phải làm sao?'})
    assert response.status_code == 200
    assert '115' in response.text
    assert 'EMERGENCY' in response.text

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

def test_rate_limit_returns_429(monkeypatch):
    from backend.app.main import limiter
    monkeypatch.setattr(limiter, 'max_requests', 1)
    limiter.requests.clear()
    try:
        payload = {'needs': [0, 0, 0, 0]}
        assert client.post('/api/learning', json=payload).status_code == 200
        response = client.post('/api/learning', json=payload)
        assert response.status_code == 429
        assert response.headers['retry-after'] == '60'
    finally:
        limiter.requests.clear()

def test_emergency_alternative_phrasing():
    for question in ['Bố tôi lơ mơ không đánh thức được phải làm sao?', 'Người thân của tôi ngừng thở rồi, phải làm gì?']:
        response = client.post('/api/chat', json={'question': question})
        assert response.status_code == 200
        assert '115' in response.json()['answer']
        assert any('EMERGENCY' in step for step in response.json()['trace'])


def test_chat_followup_passes_bounded_history(monkeypatch):
    from backend.app import main
    seen = {}
    monkeypatch.setattr(main.rag, 'standalone_question', lambda q, h: seen.update(question=q, history=h) or 'Triệu chứng tiểu đường là gì?')
    monkeypatch.setattr(main.rag, 'retrieve', lambda q, **kwargs: [{'title': 'CDC', 'url': 'https://www.cdc.gov/', 'text': 'Test', 'topic': 'Test'}])
    monkeypatch.setattr(main.rag, 'answer', lambda q, sources, history: 'Thông tin từ nguồn [1].' if history else 'Thiếu ngữ cảnh')
    conversation = [{'role': 'user', 'content': 'Tiểu đường là gì?'}, {'role': 'assistant', 'content': 'Đây là bệnh mạn tính [1].'}]
    response = client.post('/api/chat', json={'question': 'Triệu chứng của nó là gì?', 'history': conversation})
    assert response.status_code == 200
    assert response.json()['answer'] == 'Thông tin từ nguồn [1].'
    assert seen['history'] == conversation
    assert seen['question'] == 'Triệu chứng của nó là gì?'


def test_chat_rejects_overlong_history():
    history = [{'role': 'user', 'content': 'Câu hỏi cũ'}] * 11
    assert client.post('/api/chat', json={'question': 'Câu hỏi mới?', 'history': history}).status_code == 422


def test_stream_checks_rules_before_retrieval(monkeypatch):
    from backend.app import main
    monkeypatch.setattr(main.rag, 'retrieve', lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError('must not retrieve')))
    response = client.post('/api/chat/stream', json={'question': 'Tôi nên tăng liều insulin như thế nào?'})
    events = [__import__('json').loads(line) for line in response.text.splitlines()]
    assert response.status_code == 200
    assert events[0]['type'] == 'delta' and 'không thể' in events[0]['text']
    assert events[-1]['type'] == 'done' and events[-1]['sources'] == []


def test_stream_emits_fragments_and_sources(monkeypatch):
    from backend.app import main
    monkeypatch.setattr(main.rag, 'standalone_question', lambda q, h: q)
    monkeypatch.setattr(main.rag, 'retrieve', lambda *a, **k: [{'title': 'Nguồn', 'url': 'https://example.org', 'text': 'test'}])
    monkeypatch.setattr(main.rag, 'answer_parts', lambda *a: iter(['Xin ', 'chào [1].']))
    response = client.post('/api/chat/stream', json={'question': 'Tiểu đường là gì?'})
    events = [__import__('json').loads(line) for line in response.text.splitlines()]
    assert [event['text'] for event in events if event['type'] == 'delta'] == ['Xin ', 'chào [1].']
    assert events[-1]['type'] == 'done' and events[-1]['sources'][0]['title'] == 'Nguồn'
