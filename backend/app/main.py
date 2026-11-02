import logging
import os
import time
from pathlib import Path
from typing import Literal
import joblib
import numpy as np
import pandas as pd
import torch
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field, field_validator
from ml.train import Network, SYMPTOMS, BRFSS
from backend.app import rag, history
from backend.app.agents import RuleAgent, CoordinatorState
from backend.app.limiter import limiter

log = logging.getLogger(__name__)

app = FastAPI(title='Đường An — Diabetes Multi-Agent System', version='1.0.0')

# CORS support for local dev, docker web, and Cloudflare tunnel
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173', 'http://localhost:8080', 'https://diabetes.handq2212.site'],
    allow_origin_regex=r'https?://(localhost|127\.0\.0\.1|.*\.handq2212\.site)(:[0-9]+)?',
    allow_credentials=True,
    allow_methods=['GET', 'POST', 'OPTIONS'],
    allow_headers=['*'],
)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    # Enforce in-memory rate limiting on API endpoints
    if request.url.path.startswith('/api/'):
        limiter.check(request)
        
    start_time = time.time()
    response: Response = await call_next(request)
    process_time = time.time() - start_time
    
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Process-Time'] = f"{process_time:.4f}s"
    return response

ROOT = Path(os.getenv('ARTIFACTS_DIR', 'artifacts'))
DISCLAIMER = 'Công cụ học thuật nghiên cứu hệ đa tác tử, không chẩn đoán hoặc thay thế tư vấn của nhân viên y tế.'

class PredictionRequest(BaseModel):
    kind: Literal['symptoms', 'brfss']
    features: dict[str, str | float | int]

class ChatRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1500)
    
    @field_validator('question')
    @classmethod
    def no_blank(cls, value: str):
        cleaned = value.strip()
        if not cleaned:
            raise ValueError('Câu hỏi không được để trống.')
        return cleaned

class RLRequest(BaseModel):
    needs: list[Literal[0, 1]] = Field(min_length=4, max_length=4)

def validate_features(kind: str, raw: dict):
    expected = SYMPTOMS if kind == 'symptoms' else BRFSS
    if set(raw) != set(expected):
        raise ValueError('Cần nhập đầy đủ và chính xác tất cả các trường dữ liệu của biểu mẫu.')
    d = dict(raw)
    if kind == 'symptoms':
        try:
            age = float(d['age'])
        except (ValueError, TypeError):
            raise ValueError('Tuổi phải là số hợp lệ.')
        if not 1 <= age <= 120:
            raise ValueError('Tuổi phải nằm trong khoảng từ 1 đến 120.')
        d['age'] = age
        for col in SYMPTOMS[1:]:
            d[col] = str(d[col]).lower().strip()
            valid_vals = ['male', 'female'] if col == 'gender' else ['yes', 'no']
            if d[col] not in valid_vals:
                raise ValueError(f'Giá trị không hợp lệ cho trường: {col} (chọn {valid_vals})')
    else:
        allowed = {
            '_AGEG5YR': range(1, 14),
            'SEXVAR': [1, 2],
            '_SMOKER3': [1, 2, 3, 4],
            '_TOTINDA': [1, 2]
        }
        for col, values in allowed.items():
            value = str(d[col]).strip()
            if value not in [str(i) for i in values]:
                raise ValueError(f'Giá trị không hợp lệ cho trường {col}.')
            d[col] = value
        try:
            bmi = float(d['_BMI5'])
        except (ValueError, TypeError):
            raise ValueError('Chỉ số BMI phải là số hợp lệ.')
        if not 10 <= bmi <= 100:
            raise ValueError('Chỉ số BMI phải nằm trong khoảng hợp lý từ 10 đến 100.')
        d['_BMI5'] = bmi
    return d

@app.get('/api/health')
def health():
    """Live health check with granular dependency status."""
    # Check Neo4j connectivity
    neo4j_ok = False
    try:
        with rag.driver() as db:
            db.verify_connectivity()
            neo4j_ok = True
    except Exception:
        neo4j_ok = False

    # Check Ollama connectivity
    ollama_ok = False
    try:
        import httpx
        r = httpx.get(f"{rag.OLLAMA}/api/tags", timeout=3.0)
        ollama_ok = (r.status_code == 200)
    except Exception:
        ollama_ok = False

    return {
        'status': 'ok',
        'models': {
            'symptoms': (ROOT / 'symptoms' / 'model.pt').exists(),
            'brfss': (ROOT / 'brfss' / 'model.pt').exists()
        },
        'rl': (ROOT / 'rl' / 'education_policy.zip').exists(),
        'services': {
            'neo4j': neo4j_ok,
            'ollama': ollama_ok
        }
    }

@app.post('/api/predict')
def predict(req: PredictionRequest):
    """Predict diabetes risk score using PyTorch MLP."""
    try:
        features = validate_features(req.kind, req.features)
    except (ValueError, TypeError) as exc:
        raise HTTPException(422, str(exc)) from exc

    path = ROOT / req.kind
    if not (path / 'model.pt').exists() or not (path / 'preprocessor.joblib').exists():
        raise HTTPException(503, 'Chưa có mô hình đã huấn luyện. Vui lòng chạy pipeline huấn luyện.')

    try:
        pre = joblib.load(path / 'preprocessor.joblib')
        x = pre.transform(pd.DataFrame([features])).astype('float32')
        weights = torch.load(path / 'model.pt', map_location='cpu', weights_only=True)
        model = Network(weights['input_size'])
        model.load_state_dict(weights['state_dict'])
        model.eval()
        with torch.no_grad():
            score = float(torch.sigmoid(model(torch.from_numpy(x)))[0])
    except Exception as exc:
        log.exception(f"Prediction inference failure: {exc}")
        raise HTTPException(503, 'Không thể tải mô hình hoặc bộ tiền xử lý. Hãy kiểm tra artifacts.') from exc

    history.record('prediction_' + req.kind)
    trace = [
        'Coordinator',
        'Schema Validation Agent',
        f'Prediction Agent ({req.kind.upper()} PyTorch MLP)',
        'Clinical Disclaimer Decorator'
    ]
    return {
        'model': req.kind,
        'score': score,
        'classification': int(score >= 0.5),
        'threshold': 0.5,
        'trace': trace,
        'disclaimer': DISCLAIMER,
        'meaning': 'Điểm phân loại của mô hình trên tập dữ liệu nghiên cứu; không phản ánh xác suất chẩn đoán thực tế.'
    }

# LangGraph Multi-Agent Nodes
def rules_node(state: CoordinatorState) -> CoordinatorState:
    eval_result = RuleAgent.evaluate(state['question'])
    if not eval_result.passed:
        return {
            'safety_passed': False,
            'safety_category': eval_result.category,
            'safety_response': eval_result.response,
            'trace': ['Coordinator', 'Rule Agent', f"Rule Agent (Blocked: {eval_result.category})"]
        }
    return {
        'safety_passed': True,
        'trace': ['Coordinator', 'Rule Agent', 'Rule Agent (Approved)']
    }

def blocked_node(state: CoordinatorState) -> CoordinatorState:
    return {
        'answer': state.get('safety_response', 'Yêu cầu không thể thực hiện vì lý do an toàn y tế.'),
        'sources': [],
        'trace': state.get('trace', []) + ['Response Agent (Safety Directive)']
    }

def knowledge_node(state: CoordinatorState) -> CoordinatorState:
    question = state['question']
    sources = rag.retrieve(question, top_k=3, threshold=0.875)
    return {
        'sources': sources,
        'trace': state.get('trace', []) + [f"Knowledge Agent (Retrieved {len(sources)} sources)"]
    }

def response_node(state: CoordinatorState) -> CoordinatorState:
    question = state['question']
    sources = state.get('sources', [])
    answer_text = rag.answer(question, sources)
    return {
        'answer': answer_text,
        'trace': state.get('trace', []) + ['Response Agent (Cited Generation)']
    }

# Build LangGraph Coordinator
graph = StateGraph(CoordinatorState)
graph.add_node('rules', rules_node)
graph.add_node('blocked', blocked_node)
graph.add_node('knowledge', knowledge_node)
graph.add_node('response', response_node)

graph.add_edge(START, 'rules')
graph.add_conditional_edges(
    'rules',
    lambda s: 'blocked' if not s.get('safety_passed', True) else 'knowledge'
)
graph.add_edge('knowledge', 'response')
graph.add_edge('response', END)
graph.add_edge('blocked', END)

coordinator = graph.compile()

@app.post('/api/chat')
def chat(req: ChatRequest):
    """Multi-Agent Chat endpoint with LangGraph coordination."""
    try:
        result = coordinator.invoke({'question': req.question})
    except Exception as exc:
        log.exception(f"Chat pipeline error: {exc}")
        raise HTTPException(
            503,
            'Không thể truy xuất tài liệu hoặc kết nối dịch vụ Ollama/Neo4j. '
            'Vui lòng kiểm tra Docker container và dịch vụ Ollama.'
        ) from exc

    history.record('chat')
    sources_summary = [
        {'title': s['title'], 'url': s['url'], 'topic': s.get('topic', 'Y tế')}
        for s in result.get('sources', [])
    ]
    return {
        'answer': result['answer'],
        'sources': sources_summary,
        'trace': result.get('trace', ['Coordinator']),
        'disclaimer': DISCLAIMER
    }

@app.post('/api/learning')
def learning(req: RLRequest):
    """Reinforcement Learning recommendation for educational modules."""
    path = ROOT / 'rl' / 'education_policy.zip'
    from ml.rl import TOPICS

    # Handle all-zeros state: user has completed all modules
    if sum(req.needs) == 0:
        return {
            'topic': 'Tất cả các chủ đề đã hoàn thành',
            'action': -1,
            'trace': ['Coordinator', 'Learning Agent (All modules completed)'],
            'disclaimer': 'Mô phỏng giáo dục mô phỏng; không phải chỉ định điều trị y khoa.',
            'status': 'completed',
            'message': 'Người dùng giả lập đã hoàn thành tất cả 4 chủ đề giáo dục hiện có. Không cần gợi ý thêm.'
        }

    if not path.exists():
        raise HTTPException(503, 'Chưa có mô hình RL đã huấn luyện. Vui lòng huấn luyện môi trường mô phỏng.')

    try:
        from stable_baselines3 import DQN
        model = DQN.load(path)
        action, _ = model.predict(np.array(req.needs, dtype=np.int8), deterministic=True)
        chosen_action = int(action)

        # Invariant: never recommend an already completed topic if unlearned topics exist
        if req.needs[chosen_action] == 0:
            unlearned = [i for i, v in enumerate(req.needs) if v == 1]
            if unlearned:
                chosen_action = unlearned[0]

        history.record('rl_simulation')
        return {
            'topic': TOPICS[chosen_action],
            'action': chosen_action,
            'trace': ['Coordinator', 'Learning Agent (DQN Policy)'],
            'disclaimer': 'Mô phỏng giáo dục mô phỏng; không phải chỉ định điều trị y khoa.',
            'status': 'active'
        }
    except Exception as exc:
        log.exception(f"RL policy inference failure: {exc}")
        raise HTTPException(503, 'Lỗi khi thực thi mô hình học tăng cường.') from exc
