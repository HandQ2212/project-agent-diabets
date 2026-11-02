import os
import httpx
from neo4j import GraphDatabase

OLLAMA = os.getenv('OLLAMA_URL', 'http://localhost:11434').rstrip('/')
MODEL = os.getenv('OLLAMA_MODEL', 'qwen3:4b-instruct')
EMBED = os.getenv('OLLAMA_EMBED_MODEL', 'nomic-embed-text')

def embed(text):
    response = httpx.post(f'{OLLAMA}/api/embed', json={'model': EMBED, 'input': text}, timeout=90)
    response.raise_for_status()
    return response.json()['embeddings'][0]

def driver():
    return GraphDatabase.driver(os.getenv('NEO4J_URI', 'bolt://localhost:7687'), auth=(os.getenv('NEO4J_USER', 'neo4j'), os.getenv('NEO4J_PASSWORD', 'change-this-neo4j-password')))

def retrieve(question):
    vector = embed(question)
    with driver() as db:
        rows = db.execute_query('MATCH (d:Document)-[:ABOUT]->(:Topic) WHERE d.embedding IS NOT NULL WITH d, vector.similarity.cosine(d.embedding, $vector) AS score RETURN d.title AS title, d.url AS url, d.text AS text, score ORDER BY score DESC LIMIT 3', vector=vector, database_='neo4j').records
    return [dict(r) for r in rows if r['score'] is not None and r['score'] >= .25]

def answer(question, sources):
    if not sources: return 'Chưa tìm thấy tài liệu phù hợp trong kho tri thức. Vui lòng hỏi nhân viên y tế.'
    context = '\n'.join(f"[{i+1}] {s['title']} ({s['url']}): {s['text']}" for i,s in enumerate(sources))
    prompt = f"Trả lời bằng tiếng Việt, chỉ dựa trên nguồn bên dưới; trích [1], [2] tương ứng. Nếu nguồn không đủ hãy nói không biết. Không chẩn đoán, kê thuốc hoặc đưa liều dùng.\nNguồn:\n{context}\nCâu hỏi: {question}"
    resp = httpx.post(f'{OLLAMA}/api/generate', json={'model': MODEL, 'prompt': prompt, 'stream': False, 'options': {'num_ctx': 2048, 'num_predict': 350}}, timeout=180)
    resp.raise_for_status()
    return resp.json()['response']
