"""Đánh giá offline các mô hình embedding (Ollama) cho retrieval tiếng Việt của Đường An.

Không đụng Neo4j/Docker. Corpus = knowledge/sources.json + sources_v2.json (embed `text`,
giống ml/seed_knowledge.py). Câu hỏi: knowledge/eval_questions.json.

Chạy:  .venv/bin/python ml/eval_embeddings.py [--out artifacts/embedding_eval.json]
"""
import argparse, json, statistics, time
from pathlib import Path
import httpx
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OLLAMA = 'http://localhost:11434'
QWEN_INSTR = 'Instruct: Given a Vietnamese question about diabetes, retrieve relevant passages that answer it\nQuery:'
# (nhãn, model, tiền tố query, tiền tố document)
VARIANTS = [
    ('nomic (prod, không prefix)', 'nomic-embed-text', '', ''),
    ('nomic + prefix', 'nomic-embed-text', 'search_query: ', 'search_document: '),
    ('bge-m3', 'bge-m3', '', ''),
    ('snowflake-arctic-embed2', 'snowflake-arctic-embed2', 'query: ', ''),
    ('granite-embedding:278m', 'granite-embedding:278m', '', ''),
    ('qwen3-embedding:0.6b', 'qwen3-embedding:0.6b', QWEN_INSTR, ''),
]


def embed(model, texts):
    r = httpx.post(f'{OLLAMA}/api/embed', json={'model': model, 'input': texts}, timeout=600)
    r.raise_for_status()
    v = np.array(r.json()['embeddings'], dtype=np.float32)
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def load():
    docs = []
    for f in ('sources.json', 'sources_v2.json'):
        docs += json.loads((ROOT / 'knowledge' / f).read_text(encoding='utf-8'))
    qs = json.loads((ROOT / 'knowledge' / 'eval_questions.json').read_text(encoding='utf-8'))
    return docs, qs


def evaluate(label, model, qp, dp, docs, qs):
    ids = [d['id'] for d in docs]
    D = np.vstack([embed(model, [dp + d['text'] for d in docs[i:i + 8]]) for i in range(0, len(docs), 8)])
    embed(model, ['warmup'])
    ind, ood = qs['in_domain'], qs['out_of_domain']
    lat, top_in, top_ood, ranks = [], [], [], []
    for item in ind + ood:
        t = time.perf_counter()
        q = embed(model, [qp + item['q']])[0]
        lat.append((time.perf_counter() - t) * 1000)
        s = D @ q
        order = np.argsort(-s)
        if 'relevant' in item:
            top_in.append(float(s[order[0]]))
            rk = [i for i, j in enumerate(order, 1) if ids[j] in item['relevant']]
            ranks.append(min(rk))
        else:
            top_ood.append(float(s[order[0]]))
    n = len(ranks)
    r = np.array(ranks)
    res = {'label': label, 'model': model, 'dim': int(D.shape[1]),
           'hit1': float((r <= 1).mean()), 'hit3': float((r <= 3).mean()), 'mrr': float((1 / r).mean()),
           'lat_ms': statistics.median(lat),
           'in_top1': top_in, 'ood_top1': top_ood, 'ranks': ranks}
    # ngưỡng: giữ câu in-domain có top-3 chứa đúng (hit@3) và top-1 >= t; loại OOD có top-1 < t
    ti, to = np.array(top_in), np.array(top_ood)
    best = None
    rows = []
    for t in np.linspace(min(ti.min(), to.min()) - 0.01, max(ti.max(), to.max()) + 0.01, 400):
        kept = float(((ti >= t) & (r <= 3)).sum() / n)
        rej = float((to < t).mean())
        rows.append((float(t), kept, rej))
        score = (kept + rej) / 2
        if best is None or score > best[0]:
            best = (score, float(t), kept, rej)
    full_rej = [x for x in rows if x[2] == 1.0]
    t100 = min(full_rej, key=lambda x: x[0]) if full_rej else None
    res['best'] = {'thr': best[1], 'kept': best[2], 'rejected': best[3]}
    res['reject_all_ood'] = {'thr': t100[0], 'kept': t100[1]} if t100 else None
    # quét ngưỡng an toàn: top-1 OOD cao nhất + biên (margin)
    res['sweep'] = []
    for m in (0.0, 0.03, 0.06, 0.10):
        t = float(to.max()) + m + 1e-6
        res['sweep'].append({'margin': m, 'thr': t, 'kept_hit3': float(((ti >= t) & (r <= 3)).sum() / n),
                             'kept_any': float((ti >= t).mean()), 'rejected': float((to < t).mean())})
    res['stats'] = {'in_mean': float(ti.mean()), 'in_min': float(ti.min()), 'ood_mean': float(to.mean()), 'ood_max': float(to.max())}
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=str(ROOT / 'artifacts' / 'embedding_eval.json'))
    ap.add_argument('--only', default='')
    a = ap.parse_args()
    docs, qs = load()
    print(f'{len(docs)} chunks, {len(qs["in_domain"])} in-domain, {len(qs["out_of_domain"])} OOD')
    out = []
    for v in VARIANTS:
        if a.only and a.only not in v[0]:
            continue
        r = evaluate(*v, docs, qs)
        out.append(r)
        print(f"{r['label']:28s} dim={r['dim']:4d} hit@1={r['hit1']:.2f} hit@3={r['hit3']:.2f} MRR={r['mrr']:.3f} "
              f"lat={r['lat_ms']:.0f}ms in[mean={r['stats']['in_mean']:.3f},min={r['stats']['in_min']:.3f}] "
              f"ood[mean={r['stats']['ood_mean']:.3f},max={r['stats']['ood_max']:.3f}] best={r['best']} all_ood={r['reject_all_ood']}")
        for w in r['sweep']:
            print(f"    thr={w['thr']:.3f} (OODmax+{w['margin']:.2f}) kept_hit3={w['kept_hit3']:.2f} kept_any={w['kept_any']:.2f} ood_rejected={w['rejected']:.2f}")
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
