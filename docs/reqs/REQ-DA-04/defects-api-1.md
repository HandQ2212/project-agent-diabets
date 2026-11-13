# REQ-DA-04 – Defects backend (api), vòng 1

- Task: REQ-DA-04 api (Rex) – nhánh `req-da-04/api`, commit 0b1992e, 7d035cf (base 946970f), worktree `wt-da04-api`
- Tester: Hawk · Ngày: 2026-11-13 (giờ VN) · Verdict: **FAIL** (1 Medium, 1 Low)

## DEF-api-1.1 – /api/about treo ~60 s khi Neo4j nhận kết nối nhưng không trả lời (yêu cầu: timeout 3 s)

- Mức độ: **Medium** · Vị trí: `backend/app/about.py` – `kb_driver()` (chỉ đặt `connection_timeout=3.0`, `max_transaction_retry_time=0.0`) và `AboutService.get()` (giữ `_lock` trong suốt lúc `_build()`).
- Kỳ vọng: Neo4j lỗi theo **bất kỳ** kiểu nào thì `/api/about` trả 200 với `kb: null` trong khoảng 3 s (docstring của `kb_driver`: "Neo4j sập thì /api/about trả nhanh"; trọng tâm của Atlas: "timeout 3 s").
- Thực tế:
  | Kiểu lỗi Neo4j | Thời gian | Kết quả |
  |---|---|---|
  | Port đóng (connection refused) | 0,01 s | PASS |
  | IP không định tuyến được (blackhole) | 3,03 s | PASS |
  | **Nhận TCP nhưng không trả lời** (Neo4j treo, bị `docker pause`, GC dài, quá tải) | **60,2 s** | FAIL |
- Các bước tái hiện:
  1. Mở một cổng TCP nhận kết nối nhưng không gửi gì (`socket.listen()` rồi `accept()`, không trả lời).
  2. Chạy API với `NEO4J_URI=bolt://<host>:<cổng đó>` (Hawk dùng container phụ `project-api` trên :8013, mount `wt-da04-api` chỉ đọc).
  3. Gửi 3 request đồng thời `GET /api/about`.
- Evidence: `req1 200 60.195448s`, `req2 200 60.195019s`, `req3 200 60.194949s`. Probe trong tiến trình (`AboutService` + driver thật) cho kết quả tương tự: `silent-server: 60.73s kb=None`.
- Nguyên nhân (nhận định của Tester): `connection_timeout` chỉ giới hạn bước mở socket. Việc lấy connection (bolt handshake) dùng `connection_acquisition_timeout`, mặc định 60 s. Query cũng không có timeout. Vì `_lock` giữ trong lúc build, mọi request `/api/about` khác cùng chờ, và mỗi request giữ một worker thread của threadpool.
- Ảnh hưởng: trang SCR-2 hiện "Đang tải…" khoảng 60 s, vì frontend `fetchAbout` không đặt timeout. Khi web đang public qua tunnel, request dồn lại chiếm thread của API.
- Gợi ý kiểm lại (Rex quyết định cách sửa): thêm test cho kiểu lỗi "nhận TCP nhưng không trả lời" và assert thời gian ≤ 3,5 s. Có thể dùng `connection_acquisition_timeout` hoặc timeout cho query/transaction, hoặc deadline tổng cho `_kb()`.

## DEF-api-1.2 – report.json không đọc được (khác FileNotFound) làm /api/about trả 500

- Mức độ: **Low** · Vị trí: `backend/app/about.py` – `_read_json()` chỉ bắt `FileNotFoundError`; `model_info()` và `rl_info()` bắt `(KeyError, TypeError, ValueError, AttributeError)`, không bắt `OSError`.
- Kỳ vọng: docstring endpoint ghi "Luôn 200: report thiếu → metrics null". Report không đọc được cũng nên ra `metrics_test: null`.
- Thực tế: `artifacts/brfss/report.json` là thư mục, hoặc không có quyền đọc → `IsADirectoryError` / `PermissionError` lan lên thành HTTP 500. Frontend khi đó hiện trạng thái lỗi của cả trang thay vì trạng thái partial.
- Tái hiện: `AboutService(artifacts=lambda: tmp, …)` với `tmp/brfss/report.json/` là thư mục → `IsADirectoryError(21, 'Is a directory')` (probe TC-PART.2).

## Đã kiểm và đạt (không phải defect)
- Bộ test backend trong worktree: 168 passed, 25 skipped. 2 test `test_qa_benchmark` cần Neo4j/Ollama thật (lỗi `AuthError` khi chạy ngoài container) là test live mà Rex đã loại, không tính.
- Probe `AboutService` 23/24 đạt (lỗi duy nhất là DEF-api-1.2):
  - schema khớp `about.ts`; thứ tự models; `generated_at` có `+07:00`;
  - NHANES 15: threshold 0,8 và metrics bằng `test_selected_only` (roc 0,9314, f1 0,7549, recall 0,7515, precision 0,7583, CM [[1624,80],[83,251]], CI [0,913; 0,9487]);
  - 3 mô hình còn lại dùng ngưỡng 0,5, khớp `ml/train.py:84-85` và `ml/train_nhanes.py:68`;
  - cache 30 s khi KB down và 300 s khi KB ok, kiểm BVA tại 29,9 / 30,0 và 299,9 / 300,0;
  - giá trị NaN chuyển thành null; report hỏng thì trả partial;
  - không lộ `bolt`, `password`, đường dẫn máy, URL dịch vụ, `sha256`.
- Instance phụ :8012 (env lấy từ `project-api-1`, mount chỉ đọc, `STORE_DEMO_HISTORY=false`, đã xoá):
  - `/api/about` 200 trong 0,59 s, gọi lại 0,008 s (cache);
  - kb: 61 đoạn, 45 URL, `vector_index: false`, đúng vì RAG dùng `vector.similarity.cosine` chứ không có index VECTOR;
  - không có chuỗi nào bị lộ.
- Publisher: 58/58 đoạn trong `sources*.json` đều có publisher; mỗi publisher khớp tên miền và license. Trên dữ liệu thật chỉ còn 2 URL có publisher null (cdc-basics, cdc-prevention, đã biết).
- B-1/B-2/B-3 trên `/api/chat` và trên event `done` của `/api/chat/stream` (câu HbA1c):
  - `curated` kèm publisher NIDDK / Bộ Y tế / ADA;
  - `curated_graph` có `facts` kèm threshold;
  - `unreviewed_web` trả publisher null;
  - fact thiếu đầu hoặc cuối thì bị bỏ.
- Kiểm ghép:
  - SCR-2 của `wt-da04-web` (bản hiện tại 5e3ecb9) render với payload thật 16/16 đạt: số liệu thật, badge của 9 cơ quan, không có NaN / undefined / null;
  - Vite :5182 proxy sang :8012 trả `/api/about` đúng.
  - **Chưa kiểm bằng mắt** vì Chrome extension không kết nối.

## Ghi chú (không tính defect)
- `source_summary` dùng `source['title']` và `source['url']`. Trước đây `/api/chat/stream` dùng `.get()`, nên nguồn thiếu key `title` giờ sẽ làm lỗi cả event `done`. Hiện retrieve luôn có các key này nên chưa xảy ra.
