import os
from pathlib import Path
from typing import Literal
import joblib
import numpy as np
import pandas as pd
import torch
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field, field_validator
from typing_extensions import TypedDict
from ml.train import Network, SYMPTOMS, BRFSS
from backend.app import rag, history

app = FastAPI(title='Diabetes Multi-Agent Demo', version='0.1.0')
app.add_middleware(CORSMiddleware, allow_origins=['http://localhost:5173'], allow_methods=['GET','POST'], allow_headers=['*'])
ROOT = Path(os.getenv('ARTIFACTS_DIR', 'artifacts'))
DISCLAIMER = 'Công cụ học thuật, không chẩn đoán hoặc thay thế tư vấn của nhân viên y tế.'

class PredictionRequest(BaseModel):
    kind: Literal['symptoms', 'brfss']
    features: dict[str, str | float | int]

class ChatRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1500)
    @field_validator('question')
    @classmethod
    def no_blank(cls, value):
        if not value.strip(): raise ValueError('Câu hỏi không được để trống')
        return value.strip()

class RLRequest(BaseModel):
    needs: list[Literal[0, 1]] = Field(min_length=4, max_length=4)

def validate_features(kind, raw):
    expected = SYMPTOMS if kind == 'symptoms' else BRFSS
    if set(raw) != set(expected): raise ValueError('Cần nhập đầy đủ và chính xác các trường của biểu mẫu.')
    d = dict(raw)
    if kind == 'symptoms':
        age = float(d['age'])
        if not 1 <= age <= 120: raise ValueError('Tuổi phải từ 1 đến 120.')
        d['age'] = age
        for col in SYMPTOMS[1:]:
            d[col] = str(d[col]).lower()
            if d[col] not in (['male','female'] if col == 'gender' else ['yes','no']): raise ValueError(f'Giá trị không hợp lệ: {col}')
    else:
        allowed = {'_AGEG5YR': range(1,14), 'SEXVAR': [1,2], '_SMOKER3': [1,2,3,4], '_TOTINDA': [1,2]}
        for col, values in allowed.items():
            value = str(d[col])
            if value not in [str(i) for i in values]: raise ValueError(f'Giá trị không hợp lệ: {col}')
            d[col] = value
        d['_BMI5'] = float(d['_BMI5'])
        if not 10 <= d['_BMI5'] <= 100: raise ValueError('BMI phải từ 10 đến 100.')
    return d

@app.get('/api/health')
def health():
    return {'status': 'ok', 'models': {k: (ROOT/k/'model.pt').exists() for k in ['symptoms','brfss']}, 'rl': (ROOT/'rl'/'education_policy.zip').exists()}

@app.post('/api/predict')
def predict(req: PredictionRequest):
    try: features = validate_features(req.kind, req.features)
    except (ValueError, TypeError) as exc: raise HTTPException(422, str(exc)) from exc
    path = ROOT / req.kind
    if not (path/'model.pt').exists() or not (path/'preprocessor.joblib').exists(): raise HTTPException(503, 'Chưa có mô hình đã huấn luyện. Vui lòng chạy pipeline huấn luyện.')
    try:
        pre = joblib.load(path/'preprocessor.joblib')
        x = pre.transform(pd.DataFrame([features])).astype('float32')
        weights = torch.load(path/'model.pt', map_location='cpu', weights_only=True)
        model = Network(weights['input_size']); model.load_state_dict(weights['state_dict']); model.eval()
        with torch.no_grad(): score = float(torch.sigmoid(model(torch.from_numpy(x)))[0])
    except Exception as exc: raise HTTPException(503, 'Không thể tải mô hình hoặc tiền xử lý; hãy kiểm tra artifact.') from exc
    history.record('prediction_' + req.kind)
    return {'model': req.kind, 'score': score, 'classification': int(score >= .5), 'threshold': .5, 'disclaimer': DISCLAIMER, 'meaning': 'Điểm mô hình trên dữ liệu nghiên cứu; không phải xác suất chẩn đoán được kiểm chứng.'}

class State(TypedDict, total=False):
    question: str
    sources: list
    answer: str
    trace: list
    blocked: bool

def rules(state):
    text = state['question'].lower()
    blocked = any(term in text for term in ['liều thuốc', 'liều insulin', 'tăng liều', 'giảm liều', 'ngừng thuốc', 'kê thuốc'])
    return {'trace': ['Coordinator', 'Rule Agent'], 'blocked': blocked}

def blocked_response(state):
    return {'answer': 'Tôi không thể chỉ định, điều chỉnh hoặc ngừng thuốc. Hãy trao đổi với bác sĩ hoặc dược sĩ.', 'sources': [], 'trace': state['trace'] + ['Response Agent']}
def knowledge(state):
    return {'sources': rag.retrieve(state['question']), 'trace': state['trace'] + ['Knowledge Agent']}
def response(state):
    return {'answer': rag.answer(state['question'], state['sources']), 'trace': state['trace'] + ['Response Agent']}

graph = StateGraph(State)
graph.add_node('rules', rules); graph.add_node('knowledge', knowledge); graph.add_node('response', response)
graph.add_node('blocked', blocked_response)
graph.add_edge(START, 'rules'); graph.add_conditional_edges('rules', lambda s: 'blocked' if s['blocked'] else 'knowledge'); graph.add_edge('knowledge', 'response'); graph.add_edge('response', END); graph.add_edge('blocked', END)
coordinator = graph.compile()

@app.post('/api/chat')
def chat(req: ChatRequest):
    try: result = coordinator.invoke({'question': req.question})
    except Exception as exc: raise HTTPException(503, 'Không thể truy xuất tài liệu hoặc kết nối Ollama/Neo4j. Kiểm tra dịch vụ và nạp dữ liệu tri thức.') from exc
    history.record('chat')
    return {'answer': result['answer'], 'sources': [{'title': s['title'], 'url': s['url']} for s in result['sources']], 'trace': result['trace'], 'disclaimer': DISCLAIMER}

@app.post('/api/learning')
def learning(req: RLRequest):
    path = ROOT/'rl'/'education_policy.zip'
    if not path.exists(): raise HTTPException(503, 'Chưa có mô hình RL. Vui lòng huấn luyện môi trường mô phỏng.')
    from stable_baselines3 import DQN
    from ml.rl import TOPICS
    model = DQN.load(path)
    action, _ = model.predict(np.array(req.needs, dtype=np.int8), deterministic=True)
    history.record('rl_simulation')
    return {'topic': TOPICS[int(action)], 'action': int(action), 'trace': ['Coordinator', 'Learning Agent'], 'disclaimer': 'Mô phỏng giáo dục; không phải khuyến nghị điều trị.'}
