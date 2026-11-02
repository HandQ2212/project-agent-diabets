import os
import logging
import httpx
from neo4j import GraphDatabase

log = logging.getLogger(__name__)

OLLAMA = os.getenv('OLLAMA_URL', 'http://localhost:11434').rstrip('/')
MODEL = os.getenv('OLLAMA_MODEL', 'qwen3:4b-instruct')
EMBED = os.getenv('OLLAMA_EMBED_MODEL', 'nomic-embed-text')

def embed(text: str) -> list[float]:
    response = httpx.post(f'{OLLAMA}/api/embed', json={'model': EMBED, 'input': text}, timeout=90)
    response.raise_for_status()
    return response.json()['embeddings'][0]

def driver():
    return GraphDatabase.driver(
        os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
        auth=(os.getenv('NEO4J_USER', 'neo4j'), os.getenv('NEO4J_PASSWORD', 'change-this-neo4j-password'))
    )

def retrieve(question: str, top_k: int = 3, threshold: float = 0.875) -> list[dict]:
    """Retrieve top relevant documents from Neo4j knowledge graph using vector similarity."""
    try:
        vector = embed(question)
        with driver() as db:
            rows = db.execute_query(
                '''
                MATCH (d:Document)-[:ABOUT]->(t:Topic)
                WHERE d.embedding IS NOT NULL
                WITH d, t, vector.similarity.cosine(d.embedding, $vector) AS score
                RETURN d.id AS id, d.title AS title, d.url AS url, d.text AS text,
                       d.date AS date, d.license AS license, t.name AS topic, score
                ORDER BY score DESC LIMIT $top_k
                ''',
                vector=vector,
                top_k=top_k,
                database_='neo4j'
            ).records
        
        # Filter by threshold to avoid returning irrelevant documents
        results = [dict(r) for r in rows if r['score'] is not None and r['score'] >= threshold]
        return results
    except Exception as exc:
        log.exception(f"Error during RAG retrieval: {exc}")
        raise

def answer(question: str, sources: list[dict]) -> str:
    """Generate grounded, cited Vietnamese answer based exclusively on retrieved sources."""
    if not sources:
        return (
            "Chưa tìm thấy tài liệu phù hợp trong kho tri thức của hệ thống cho câu hỏi này. "
            "Đây là hệ thống học thuật và không tự suy diễn thông tin y tế khi thiếu tài liệu kiểm chứng. "
            "Vui lòng tham khảo ý kiến bác sĩ hoặc cơ sở y tế chuyên khoa."
        )

    context = '\n\n'.join(
        f"[{i+1}] {s['title']} ({s.get('topic', 'Y tế')}) - Nguồn: {s['url']}\nNội dung: {s['text']}"
        for i, s in enumerate(sources)
    )

    prompt = f"""Bạn là trợ lý thông tin y tế học thuật về bệnh đái tháo đường.
Nhiệm vụ của bạn là giải thích thông tin một cách chính xác, khách quan và dễ hiểu bằng tiếng Việt CHỈ DỰA TRÊN các nguồn tài liệu được cung cấp dưới đây.

Nguồn tài liệu:
{context}

Câu hỏi người dùng:
{question}

Quy tắc bắt buộc:
1. Trả lời bằng tiếng Việt, súc tích và có cấu trúc rõ ràng.
2. Mọi thông tin phát biểu đều phải có trích dẫn nguồn tương ứng bằng ký hiệu số như [1], [2] ở cuối câu.
3. Nếu các nguồn trên không chứa đủ thông tin để trả lời câu hỏi, hãy nêu rõ rằng tài liệu hiện có chưa đề cập nội dung này. Tuyệt đối không tự sáng tác thêm thông tin y tế ngoài nguồn.
4. Tuyệt đối không đưa ra chẩn đoán xác định, không kê đơn thuốc, không chỉ định liều lượng cụ thể. Luôn giữ tinh thần cung cấp kiến thức học tập."""

    try:
        resp = httpx.post(
            f'{OLLAMA}/api/generate',
            json={
                'model': MODEL,
                'prompt': prompt,
                'stream': False,
                'options': {'num_ctx': 4096, 'num_predict': 500, 'temperature': 0.1}
            },
            timeout=180
        )
        resp.raise_for_status()
        return resp.json()['response'].strip()
    except Exception as exc:
        log.exception(f"Error during LLM answer generation: {exc}")
        raise
