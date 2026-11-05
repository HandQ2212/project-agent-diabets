import logging
import json
import os
import time
import math
from pathlib import Path
from typing import Literal
import joblib
import numpy as np
import pandas as pd
import torch
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field, field_validator
from ml.train import Network, SYMPTOMS, BRFSS
from ml.train_nhanes import ClinicalCNN, FEATURES as NHANES_FEATURES
from backend.app import rag, history, nhanes15
from backend.app.agents import RuleAgent, CoordinatorState, conversational_reply
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
        try:
            limiter.check(request)
        except HTTPException as exc:
            return JSONResponse(status_code=exc.status_code, content={'detail': exc.detail}, headers={'Retry-After': str(limiter.window_seconds)})
        
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
    kind: Literal['symptoms', 'brfss', 'nhanes_research', 'nhanes15_research']
    features: dict[str, str | float | int]

class ChatMessage(BaseModel):
    role: Literal['user', 'assistant']
    content: str = Field(min_length=1, max_length=1500)

class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=1500)
    history: list[ChatMessage] = Field(default_factory=list, max_length=10)
    
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
    if kind == 'nhanes15_research':
        if set(raw) != set(nhanes15.FEATURES):
            raise ValueError('Cần nhập đủ 15 chỉ số của ví dụ nghiên cứu.')
        result = {}
        for key, (low, high) in nhanes15.BOUNDS.items():
            try:
                value = float(raw[key])
            except (TypeError, ValueError):
                raise ValueError(f'{key} phải là số hợp lệ.')
            if not math.isfinite(value) or not low <= value <= high or (key == 'RIAGENDR' and value not in (1, 2)):
                raise ValueError(f'{key} phải nằm trong khoảng {low}–{high}.')
            result[key] = value
        return result
    if kind == 'nhanes_research':
        if set(raw) != set(NHANES_FEATURES):
            raise ValueError('Cần nhập đủ bốn chỉ số của ví dụ nghiên cứu.')
        bounds = {'RIDAGEYR': (18, 80), 'BMXBMI': (10, 100), 'LBXGLU': (40, 500), 'LBXGH': (3, 20)}
        result = {}
        for key, (low, high) in bounds.items():
            try:
                value = float(raw[key])
            except (TypeError, ValueError):
                raise ValueError(f'{key} phải là số hợp lệ.')
            if not math.isfinite(value) or not low <= value <= high:
                raise ValueError(f'{key} phải nằm trong khoảng {low}–{high}.')
            result[key] = value
        return result
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
            'brfss': (ROOT / 'brfss' / 'model.pt').exists(),
            'nhanes_research': (ROOT / 'nhanes_research' / 'model.pt').exists() and (ROOT / 'nhanes_research' / 'scaler.joblib').exists(),
            'nhanes15_research': all((ROOT / 'nhanes15_web' / f).exists() for f in ('neural_seed_42.pt', 'preprocessor.joblib', 'report.json')),
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

    path = ROOT / ('nhanes15_web' if req.kind == 'nhanes15_research' else req.kind)
    if req.kind == 'nhanes15_research':
        try:
            report = json.loads((path / 'report.json').read_text(encoding='utf-8'))
            if report['selected_model'] != 'neural_seed_42' or report['features'] != nhanes15.FEATURES:
                raise ValueError('Selected model or feature order mismatch')
            threshold = float(report['selected_threshold'])
            if not math.isfinite(threshold) or not 0 <= threshold <= 1:
                raise ValueError('Invalid selected threshold')
            pre = joblib.load(path / 'preprocessor.joblib')
            x = pre.transform(pd.DataFrame([features], columns=nhanes15.FEATURES)).astype('float32')
            weights = torch.load(path / 'neural_seed_42.pt', map_location='cpu', weights_only=True)
            if weights['architecture'] != 'CNN' or weights['input_size'] != x.shape[1]:
                raise ValueError('Model architecture or input size mismatch')
            model = nhanes15.NotebookCNN(x.shape[1])
            model.load_state_dict(weights['state_dict']); model.eval()
            with torch.no_grad():
                score = float(torch.sigmoid(model(torch.from_numpy(x)))[0])
        except Exception as exc:
            log.exception('NHANES 15 inference failed')
            raise HTTPException(503, 'Chưa thể tải mô hình NHANES 15 chỉ số và bộ tiền xử lý tương ứng.') from exc
        history.record('prediction_nhanes15_research')
        return {
            'model': req.kind, 'score': score, 'classification': int(score >= threshold),
            'threshold': threshold,
            'trace': ['Coordinator', 'Kiểm tra dữ liệu đầu vào', 'Prediction Agent (NHANES 15 CNN 1D, seed 42)', 'Thông báo giới hạn học thuật'],
            'disclaimer': DISCLAIMER,
            'meaning': 'Mô phỏng nhãn khảo sát về chẩn đoán trước đó trong dữ liệu NHANES Hoa Kỳ; không dự báo bệnh mới, không dùng để sàng lọc hay chẩn đoán.',
        }
    preprocessor = 'scaler.joblib' if req.kind == 'nhanes_research' else 'preprocessor.joblib'
    if not (path / 'model.pt').exists() or not (path / preprocessor).exists():
        raise HTTPException(503, 'Chưa có mô hình đã huấn luyện. Vui lòng chạy pipeline huấn luyện.')

    try:
        pre = joblib.load(path / preprocessor)
        x = pre.transform(pd.DataFrame([features], columns=NHANES_FEATURES if req.kind == 'nhanes_research' else None)).astype('float32')
        weights = torch.load(path / 'model.pt', map_location='cpu', weights_only=True)
        model = ClinicalCNN() if req.kind == 'nhanes_research' else Network(weights['input_size'])
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
        'Kiểm tra dữ liệu đầu vào',
        f"Prediction Agent ({req.kind.upper()} PyTorch {'CNN 1D' if req.kind == 'nhanes_research' else 'MLP'})",
        'Thông báo giới hạn học thuật'
    ]
    return {
        'model': req.kind,
        'score': score,
        'classification': int(score >= 0.5),
        'threshold': 0.5,
        'trace': trace,
        'disclaimer': DISCLAIMER,
        'meaning': ('Mô phỏng phân loại câu trả lời khảo sát về chẩn đoán trước đó, dựa trên các chỉ số đo cùng thời điểm. Không dự báo bệnh mới, không dùng để sàng lọc hay chẩn đoán.' if req.kind == 'nhanes_research' else 'Điểm phân loại của mô hình trên tập dữ liệu nghiên cứu; không phản ánh xác suất chẩn đoán thực tế.')
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

def conversation_node(state: CoordinatorState) -> CoordinatorState:
    return {
        'answer': conversational_reply(state['question']),
        'sources': [],
        'trace': state.get('trace', []) + ['Conversation Agent'],
    }

def knowledge_node(state: CoordinatorState) -> CoordinatorState:
    question = state['question']
    search_question = rag.standalone_question(question, state.get('history', []))
    sources = rag.retrieve(search_question, top_k=3, threshold=0.875)
    return {
        'sources': sources,
        'trace': state.get('trace', []) + [f"Knowledge Agent (Retrieved {len(sources)} sources)"]
    }

def response_node(state: CoordinatorState) -> CoordinatorState:
    question = state['question']
    sources = state.get('sources', [])
    answer_text = rag.answer(question, sources, state.get('history', []))
    links_only = bool(sources) and all(source.get('review_status') == 'unreviewed_web' for source in sources)
    response_step = 'Response Agent (No source)' if not sources else ('Response Agent (Links to unreviewed sources)' if links_only else 'Response Agent (Cited Generation)')
    return {
        'answer': answer_text,
        'trace': state.get('trace', []) + [response_step]
    }

# Build LangGraph Coordinator
graph = StateGraph(CoordinatorState)
graph.add_node('rules', rules_node)
graph.add_node('blocked', blocked_node)
graph.add_node('conversation', conversation_node)
graph.add_node('knowledge', knowledge_node)
graph.add_node('response', response_node)

graph.add_edge(START, 'rules')
graph.add_conditional_edges(
    'rules',
    lambda s: 'blocked' if not s.get('safety_passed', True) else ('conversation' if conversational_reply(s['question']) else 'knowledge')
)
graph.add_edge('conversation', END)
graph.add_edge('knowledge', 'response')
graph.add_edge('response', END)
graph.add_edge('blocked', END)

coordinator = graph.compile()

@app.post('/api/chat')
def chat(req: ChatRequest):
    """Multi-Agent Chat endpoint with LangGraph coordination."""
    try:
        result = coordinator.invoke({'question': req.question, 'history': [message.model_dump() for message in req.history]})
    except Exception as exc:
        log.exception(f"Chat pipeline error: {exc}")
        raise HTTPException(
            503,
            'Không thể truy xuất tài liệu hoặc kết nối dịch vụ Ollama/Neo4j. '
            'Vui lòng kiểm tra Docker container và dịch vụ Ollama.'
        ) from exc

    history.record('chat')
    sources_summary = [
        {'title': s['title'], 'url': s['url'], 'topic': s.get('topic', 'Y tế'),
         'review_status': s.get('review_status'), 'fetched_at': s.get('fetched_at')}
        for s in result.get('sources', [])
    ]
    return {
        'answer': result['answer'],
        'sources': sources_summary,
        'trace': result.get('trace', ['Coordinator']),
        'disclaimer': DISCLAIMER
    }

@app.post('/api/chat/stream')
def chat_stream(req: ChatRequest):
    """Stream answer fragments over HTTP after the same input safety checks."""
    def event(kind, **payload):
        return json.dumps({'type': kind, **payload}, ensure_ascii=False) + '\n'

    def generate():
        try:
            state = {'question': req.question, 'history': [m.model_dump() for m in req.history]}
            state.update(rules_node(state))
            if not state['safety_passed']:
                state.update(blocked_node(state))
                yield event('delta', text=state['answer'])
            elif conversational_reply(state['question']):
                state.update(conversation_node(state))
                yield event('delta', text=state['answer'])
            else:
                state.update(knowledge_node(state))
                sources = state['sources']
                for part in rag.answer_parts(req.question, sources, state['history']):
                    yield event('delta', text=part)
                links_only = bool(sources) and all(s.get('review_status') == 'unreviewed_web' for s in sources)
                step = 'Response Agent (No source)' if not sources else ('Response Agent (Links to unreviewed sources)' if links_only else 'Response Agent (Cited Generation)')
                state['trace'].append(step)
            history.record('chat')
            summary = [{k: s.get(k) for k in ('title', 'url', 'topic', 'review_status', 'fetched_at')} for s in state.get('sources', [])]
            yield event('done', sources=summary, trace=state['trace'], disclaimer=DISCLAIMER)
        except Exception:
            log.exception('Streaming chat pipeline error')
            yield event('error', message='Không thể hoàn tất câu trả lời. Vui lòng kiểm tra Ollama và Neo4j rồi thử lại.')

    return StreamingResponse(generate(), media_type='application/x-ndjson', headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})

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
        overridden = req.needs[chosen_action] == 0
        if overridden:
            unlearned = [i for i, v in enumerate(req.needs) if v == 1]
            if unlearned:
                chosen_action = unlearned[0]

        history.record('rl_simulation')
        return {
            'topic': TOPICS[chosen_action],
            'action': chosen_action,
            'trace': ['Coordinator', 'Learning Agent (DQN Policy)' + (' → quy tắc chọn chủ đề chưa học' if overridden else '')],
            'policy_overridden': overridden,
            'disclaimer': 'Mô phỏng giáo dục mô phỏng; không phải chỉ định điều trị y khoa.',
            'status': 'active'
        }
    except Exception as exc:
        log.exception(f"RL policy inference failure: {exc}")
        raise HTTPException(503, 'Lỗi khi thực thi mô hình học tăng cường.') from exc
