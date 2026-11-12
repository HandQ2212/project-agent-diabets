# Đánh giá mô hình embedding cho RAG tiếng Việt (Đường An)

## 1. Bối cảnh và cách đánh giá
`retrieve()` trong `backend/app/rag.py` embed câu hỏi bằng `nomic-embed-text` rồi giữ Document Neo4j có cosine >= 0.875. Thực tế câu hỏi tiếng Việt hay lấy sai đoạn, và câu ngoài miền (món phở) vẫn vượt ngưỡng. Nomic thiên về tiếng Anh.

Đánh giá chạy hoàn toàn offline (không Neo4j/Docker), chỉ gọi Ollama:
- Corpus: 43 chunk (`knowledge/sources.json` 18 + `knowledge/sources_v2.json` 25), embed `text` như `ml/seed_knowledge.py`.
- Bộ câu hỏi `knowledge/eval_questions.json`: 41 câu trong miền (ngắn/dài, có/không dấu, "tiểu đường"/"đái tháo đường", triệu chứng kể chuyện), mỗi câu gắn 1-3 chunk đúng; 10 câu ngoài miền (nấu ăn, bóng đá, code, thời tiết, vàng, Windows, chính trị, du lịch, tiếng Anh, trồng rau).
- Script: `.venv/bin/python ml/eval_embeddings.py` (tái dùng được; thêm mô hình ở `VARIANTS`). Cosine tính trên vector đã chuẩn hóa, xếp hạng toàn bộ 43 chunk.
- Prefix: nomic thử có/không `search_query:`/`search_document:`; snowflake-arctic-embed2 dùng `query: `; qwen3-embedding dùng instruction cho query; bge-m3 và granite không prefix.
- Mô hình tải thêm: bge-m3 (1.2 GB), snowflake-arctic-embed2 (1.2 GB), qwen3-embedding:0.6b (0.64 GB), granite-embedding:278m (0.56 GB), tổng khoảng 3.6 GB (hơi vượt mốc 3 GB do thử 4 mô hình; có thể `ollama rm` mô hình không chọn).

## 2. Kết quả
| Mô hình | Dim | hit@1 | hit@3 | MRR | cosine top-1 in-domain (TB / min) | cosine top-1 ngoài miền (TB / max) | Độ trễ/query (median) |
|---|---|---|---|---|---|---|---|
| nomic-embed-text (production, không prefix) | 768 | 0.46 | 0.59 | 0.567 | 0.827 / 0.759 | 0.749 / 0.804 | 21 ms |
| nomic-embed-text + prefix | 768 | 0.49 | 0.61 | 0.580 | 0.788 / 0.714 | 0.735 / 0.782 | 23 ms |
| **bge-m3** | 1024 | **0.93** | **0.95** | 0.941 | 0.720 / 0.377 | 0.369 / 0.439 | 35 ms |
| snowflake-arctic-embed2 | 1024 | **0.93** | **0.95** | **0.943** | 0.660 / 0.254 | 0.221 / 0.309 | 39 ms |
| qwen3-embedding:0.6b | 1024 | 0.85 | 0.95 | 0.906 | 0.784 / 0.562 | 0.360 / 0.419 | 36 ms |
| granite-embedding:278m | 768 | 0.71 | 0.80 | 0.778 | 0.862 / 0.673 | 0.625 / 0.684 | 21 ms |

(Độ trễ đo khi máy đang có job nặng khác chạy CPU, chỉ mang tính tương đối; mỗi query là một lần gọi `/api/embed`.)

### Tách điểm trong/ngoài miền và ngưỡng
Ngưỡng được quét với tiêu chí: loại hết 10 câu ngoài miền, giữ tối đa câu trong miền có đáp án đúng trong top-3 ("giữ hit@3").

| Mô hình | Ngưỡng tối thiểu loại 100% ngoài miền | Giữ hit@3 tại ngưỡng đó | Ghi chú đánh đổi |
|---|---|---|---|
| nomic (production) | 0.804 | 56% | Ngưỡng 0.875 hiện tại giữ gần như 0 câu đúng (tại 0.864 chỉ 15%): trong miền và ngoài miền gần như chồng nhau (0.759-0.90 so với 0.749-0.804). |
| nomic + prefix | 0.782 | 44% | Tệ hơn khi lọc. |
| bge-m3 | 0.439 | 95% | Giữ nguyên 95% đến tận 0.54; biên an toàn rộng. Ngưỡng 0.50: giữ 95%, loại 100%. |
| snowflake-arctic-embed2 | 0.309 | 95% | Giữ 95% đến 0.41 (93% ở 0.409); thang điểm thấp hơn. |
| qwen3-embedding:0.6b | 0.419 | 95% (100% câu có top-1 trên ngưỡng) | Tách tốt nhất (in-domain min 0.562 > ngoài miền max 0.419) nhưng hit@1 thấp hơn (0.85). |
| granite-embedding:278m | 0.684 | 80% | Tách yếu, retrieval kém. |

Câu hỏi còn sai ở bge-m3: hai câu không dấu ("Duong huyet luc doi bao nhieu...", "an nhieu uong nhieu tieu nhieu sut can...") và một câu "Đái tháo đường có những loại nào?" (đáp án đứng hạng 2). Chính hai câu không dấu này kéo cosine thấp nhất xuống 0.377, thấp hơn mức ngoài miền cao nhất; còn lại câu trong miền đều >= 0.5. Tức là câu không dấu hiện không được giữ bởi ngưỡng nào. Nomic lấy sai nhiều câu trọng tâm (hạ đường huyết hạng 6, đường huyết lúc đói hạng 13, "run tay vã mồ hôi" hạng 32).

## 3. Khuyến nghị
**Dùng `bge-m3` với ngưỡng 0.50** (top_k giữ 3). Lý do: hit@1 0.93/hit@3 0.95 (so với 0.46/0.59), loại sạch 10/10 câu ngoài miền với biên 0.06 trên điểm ngoài miền cao nhất, không prefix nên ít thay đổi code, mô hình phổ biến, đa ngôn ngữ, ~35 ms/query. `snowflake-arctic-embed2` ngang chất lượng nhưng cần prefix `query: ` ở phía query (code `embed()` phải phân biệt query/document). `qwen3-embedding:0.6b` là phương án nhẹ hơn (0.64 GB), tách miền tốt nhất, đổi lại xếp hạng top-1 kém hơn, và cần instruction cho query.

Lưu ý giới hạn: chỉ 10 câu ngoài miền và 41 câu trong miền, một người viết; ngưỡng 0.50 nên được kiểm lại bằng log hỏi đáp thật. Điểm cosine của mỗi mô hình có thang riêng, không dùng chung ngưỡng giữa các mô hình. Chunk tiếng Anh từ `web_sources` (có `web_source_id`, truy vấn bằng bản dịch) chưa nằm trong đánh giá này.

## 4. Thay đổi code/cấu hình cần làm (chưa thực hiện)
1. Tải mô hình: `ollama pull bge-m3` (trên máy chạy Ollama của stack).
2. Biến môi trường `OLLAMA_EMBED_MODEL=bge-m3` trong `docker-compose.yml` (service backend) và `.env.example`; `backend/app/rag.py` đã đọc biến này (mặc định hiện vẫn là `nomic-embed-text`, nên đổi mặc định luôn).
3. Số chiều vector đổi 768 -> 1024. Nếu có vector index trong Neo4j (`CREATE VECTOR INDEX ... vector.dimensions`) thì phải xóa và tạo lại với 1024; nếu chỉ dùng `vector.similarity.cosine` trên thuộc tính `embedding` như `retrieve()` hiện tại thì không cần index, chỉ cần dữ liệu mới.
4. Nạp lại (re-seed): chạy lại `ml/seed_knowledge.py` (và `ml/refresh_web.py` cho chunk web) để ghi đè `d.embedding` bằng vector 1024 chiều. Không được trộn vector cũ 768 chiều với vector mới, vì cosine giữa hai kích thước khác nhau lỗi hoặc vô nghĩa. Nên đặt thuộc tính `embedding_model` trên Document để kiểm tra.
5. Ngưỡng: đổi 0.875 thành 0.50 ở mặc định `threshold` của `retrieve()` trong `backend/app/rag.py` và ở chỗ gọi trong `knowledge_node` của `backend/app/main.py` (nếu truyền cứng). Nên đưa ra biến môi trường `RAG_THRESHOLD`. Ngưỡng cũng ảnh hưởng `_topic_boost` (điều kiện `score >= 0.84` và boost +0.08 đang hiệu chỉnh cho thang nomic): cần chỉnh lại (ví dụ `score >= 0.45`, boost nhỏ hơn) hoặc bỏ boost và chạy lại đánh giá.
6. Test: `backend/tests/test_qa_benchmark.py` và các test dựa trên ngưỡng cũ cần cập nhật; chạy lại `ml/eval_embeddings.py` sau khi thêm chunk mới để theo dõi.
7. Câu không dấu: cân nhắc chuẩn hóa/khôi phục dấu hoặc thêm từ khóa không dấu vào chunk, vì đây là điểm yếu còn lại của mọi mô hình.

## 5. Đã áp dụng (12/11/2026)
- `backend/app/rag.py`: mặc định `OLLAMA_EMBED_MODEL=bge-m3`; ngưỡng là `RAG_THRESHOLD` (env, mặc định `DEFAULT_THRESHOLD=0.50`, giá trị sai ngoài 0..1 thì dùng mặc định và cảnh báo); `retrieve(threshold=None)` dùng ngưỡng này, `main.py` không còn truyền cứng 0.875.
- **Phát hiện thang điểm**: `vector.similarity.cosine` của Neo4j trả `(1+cos)/2`, không phải cosine thuần. Vì vậy 0.875 cũ tương đương cosine 0.75 và ngưỡng 0.50 của tài liệu này (cosine thuần) phải quy đổi: truy vấn nay tính `2*score-1`. Nếu không quy đổi, câu "phở bò" vẫn qua ngưỡng (điểm Neo4j 0.69).
- `_topic_boost`: giữ cơ chế, hiệu chỉnh theo cosine thuần: cộng `TOPIC_BOOST=0.10` khi điểm >= ngưỡng - `TOPIC_BOOST_MARGIN=0.05` (cũ 0.08/0.035 trên thang (1+cos)/2 ~ 0.16/0.07 cosine; bge-m3 thang hẹp hơn). Với bge-m3, câu "loại + phòng ngừa" đã đạt 0.70 nên boost gần như không còn cần thiết nhưng vẫn vô hại (cần khớp từ khóa cả câu hỏi và chủ đề).
- Không trộn vector khác chiều: `seed_knowledge.py` và `refresh_web.py` ghi `embedding_model`; `retrieve` chỉ so với Document có `embedding_model` = mô hình hiện tại và `size(embedding)` = số chiều vector truy vấn, nếu không có Document nào phù hợp thì log cảnh báo nhắc re-seed. `refresh_web` không còn bỏ qua nguồn "nội dung không đổi" nếu còn đoạn embed bằng mô hình khác. Neo4j không có vector index (chỉ RANGE/LOOKUP), nên không cần tạo lại index.
- Đã nạp lại: `ml.seed_knowledge` (43 doc), `ml.seed_graph` (48 thực thể/53 quan hệ), `ml.refresh_web` (190 chunk web). Còn 3 Document cũ không có trong `sources*.json` (`who-diabetes`, `cdc-basics`, `cdc-prevention`, 768 chiều) bị loại khỏi truy vấn; chưa xóa.
- Test: `backend/tests/test_rag_threshold.py` (ngưỡng, env, boost, lệch model/chiều, cảnh báo).
