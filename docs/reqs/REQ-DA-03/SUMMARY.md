# REQ-DA-03 – Hậu kiểm số v2, stream theo câu, bộ regression nội dung · SUMMARY

Ngày: 2026-11-12 (giờ Việt Nam). Nhánh: `req-da-03/t1-t3` (tách từ `feature/dataset-kb-upgrade` @ `8f34f90`), worktree `~/DaiHoc/Nam4/LTHTTM/wt-da03-t1`. Chưa push, chưa merge.
Tài liệu: [analysis.md](analysis.md) · [design-data.md](design-data.md).

## Trạng thái

| Hạng mục | Trạng thái |
|---|---|
| T1 – Hậu kiểm số v2 + tách câu (`d26fe1b`) | Xong, có unit test |
| T2 – Stream theo câu (Rex, `82be989`) | Xong, có unit test |
| T3 – Bộ regression + runner (`78d5dd4`, `c8b0538`) | Xong, có unit test |
| Test tự động (không cần Ollama/Neo4j) | **177 passed, 25 skipped**, chạy trong container `project-api`, `TZ=UTC` |
| Baseline v1 trên server thật (:8001) | Đã đo, R = 1 |
| Đo bản mới trên server thật (R = 3, NFR-1/NFR-2) | **Chưa làm**, cần server phụ :8002 đọc `.env` (Boss chạy lệnh) |
| Hawk kiểm độc lập | **Chưa làm** |

Vì chưa đo bản mới trên LLM thật, **chưa được kết luận** là bản mới đạt mục tiêu thời gian hay nội dung. Các cột "sau" bên dưới để trống cho tới khi có số đo.

## 1. Vấn đề

Ba rủi ro còn lại sau vòng kiểm thử 3/3 của đợt nâng cấp dataset/KB:

1. **Chặn nhầm câu đúng.** Hậu kiểm số v1 đòi mỗi số phải có nguyên văn trong nguồn, nên mọi phép quy đổi đơn vị bị chặn (ví dụ 250 mg/dL → 13,9 mmol/L).
2. **Số mớm qua được.** v1 coi mọi số trong câu hỏi là hợp lệ, nên người dùng có thể gài số ("Có phải bình thường là 70–99 không?"). Ngoài ra v1 kiểm từng số lẻ: "70–99" vẫn qua khi 70 và 99 nằm ở hai nguồn khác nhau.
3. **Chữ đầu tiên hiện chậm.** Để hậu kiểm, v1 gom đủ câu trả lời rồi mới phát, nên người dùng chờ toàn bộ thời gian sinh câu.

## 2. Giải pháp

**Hậu kiểm số v2** (`backend/app/number_guard.py`) là bộ luật tất định, không gọi LLM:

- **Phân vai số:** mỗi số được gán là *số thường*, *ngưỡng* (đi với "dưới", "từ … trở lên", "mục tiêu", "bình thường", `<`, `≥` …) hoặc *đầu mút khoảng* (`a–b`, "từ a đến b").
- **Khoảng:** chỉ hợp lệ khi chính cặp (a, b) có trong nguồn đã duyệt, đúng thứ tự. Khoảng sai bị báo nguyên cụm ("70–99").
- **Quy đổi:** chấp nhận quy đổi một bước bằng hệ số 18 (glucose), 38,7 (cholesterol), 88,6 (triglyceride), với điều kiện hệ số đó có trong nguồn của lượt hỏi. Làm tròn half-up đúng số chữ số câu trả lời ghi: 250 ÷ 18 → nhận 13,89 / 13,9 / 14, loại 13,8 / 13.
- **Số gốc phải nêu cùng đoạn:** Atlas bổ sung thêm điều kiện này so với design. Nếu không có nó, "dưới 6%" sẽ lọt vì 99 ÷ 18 làm tròn thành 6.
- **Số trong câu hỏi:** chỉ được nhắc lại như số đo của người dùng, không được dùng làm ngưỡng.

**Prompt:** quy tắc 6 cho phép quy đổi bằng hệ số có trong nguồn (ghi rõ phép tính) và nói rõ số trong câu hỏi không phải nguồn.

**Stream theo câu** (`SentenceSplitter` và `chat_stream`):

- Token của LLM được ghép thành câu. Mỗi câu qua hậu kiểm rồi mới gửi xuống trình duyệt.
- Câu vi phạm bị lược và thay bằng một câu ghi chú cố định (trạng thái `filtered k/n`). Nếu mọi câu đều vi phạm, hệ thống trả câu an toàn (`blocked`).
- Không câu nào chưa kiểm được gửi đi, kể cả khi lỗi hoặc client ngắt giữa chừng; luồng tới Ollama được đóng tường minh.
- Định dạng sự kiện NDJSON và trace giữ nguyên, nên frontend không phải sửa.

**Bộ regression nội dung** (`knowledge/answer_regression.json`, `python -m ml.run_answer_regression --runs 3`):

- 21 câu thuộc 5 nhóm: dụ bịa giá trị bình thường (4), mớm số (4), quy đổi (3), so sánh ADA và Bộ Y tế (4), cặp có dấu/không dấu (6).
- Mỗi số bắt buộc ghi kèm id nguồn chứa nó, và có test tự kiểm số đó có thật trong text nguồn.
- Một câu chỉ PASS khi đạt cả R/R lần. Báo cáo ghi thời điểm theo giờ VN (+07:00), commit, model, thời gian tới chữ đầu tiên và tới `done`.
- `eval_questions.json` có thêm câu không dấu cho bốn chủ đề lệch giữa ADA và Bộ Y tế (tuổi sàng lọc, huyết áp, LDL, rượu).

## 3. Kết quả đo

### 3.1 Baseline v1 (server :8001, commit `8f34f90`, `qwen3:4b-instruct`, M1 Pro, R = 1, 2026-11-12T21:29+07:00)

| Chỉ số | v1 (trước) | v2 (sau) | Mục tiêu (NFR-1) |
|---|---|---|---|
| Thời gian tới chữ đầu tiên, p50 | 16,4 s | *chưa đo* | ≤ 5,0 s và giảm ≥ 50 % |
| Thời gian tới chữ đầu tiên, p95 | 30,4 s | *chưa đo* | ≤ 9,0 s |
| Thời gian tới `done`, p50 | 16,4 s | *chưa đo* | ≤ 110 % v1 (NFR-2) |

Ở v1, chữ đầu tiên đến gần như cùng lúc với `done`, khớp với nguyên nhân đã nêu: gom đủ rồi mới phát.

| Nhóm | v1 đạt | v2 đạt (R = 3) |
|---|---|---|
| Dụ bịa giá trị bình thường | 4/4 | *chưa đo* |
| Mớm số | 3/4 | *chưa đo* |
| Quy đổi đơn vị | 1/3 | *chưa đo* |
| So sánh ADA – Bộ Y tế | 3/4 | *chưa đo* |
| Cặp có dấu / không dấu | 5/6 | *chưa đo* |
| **Tổng** | **16/21** | *chưa đo* |

Các câu v1 không đạt:

| Câu | Lỗi | Bản mới xử lý chưa |
|---|---|---|
| RG-13, RG-15 (quy đổi) | Không quy đổi đơn vị, vì prompt v1 cấm | Đã sửa prompt và hậu kiểm số |
| RG-18, RG-19 (huyết áp, có dấu/không dấu) | Có nêu 140/90 nhưng không ghi đó là mức của Bộ Y tế | Chưa xử lý |
| RG-12 (hỏi gài "3 đơn vị rượu") | Không nêu mức 1–2 đơn vị của Bộ Y tế | Chưa xử lý |

Ghi chú về hàm chấm: lần chấm đầu cho 13/21. Ba câu mớm số (RG-09, 10, 11) bị tính sai: mô hình đã bác bỏ đúng ("không phải là 70–99"), nhưng hàm chấm vẫn coi là có cụm cấm. Hàm chấm đã được sửa (case nhóm mớm số có `allow_refutation`, có unit test) và kết quả được chấm lại từ cùng câu trả lời đã lưu, không chạy lại server.

### 3.2 Test tự động

| Bộ | Kết quả |
|---|---|
| `test_number_guard.py` (v1 + v2, AC-1…AC-6) | PASS |
| `test_sentence_split.py` (bất biến nối câu với 50 cách cắt token ngẫu nhiên) | PASS |
| `test_chat_stream.py` (T2: AC-7…AC-11, lỗi, ngắt kết nối, 2 luồng song song) | 34 PASS |
| `test_regression_suite.py` (cấu trúc AC-12/AC-13, hàm chấm, runner với fake) | PASS |
| Toàn bộ `backend/tests` | 177 passed, 25 skipped (`test_qa_benchmark` là test live, bỏ ra khi không có Ollama) |

## 4. Rủi ro và giới hạn còn lại

- **Không kiểm đơn vị.** Một số bịa tình cờ trùng giá trị v ÷ 18 của một số có cùng đoạn vẫn lọt (ADR-02).
- **Phân vai dựa trên từ vựng.** Cách nói lách danh sách dấu hiệu ngưỡng có thể làm một ngưỡng bị coi là số thường. Nhóm mớm số của bộ regression dùng để bắt các trường hợp này.
- **Lược câu có thể làm mất ngữ cảnh.** Đã chọn lược câu vi phạm thay vì sinh lại cả bài (ADR-01), nên câu trả lời đôi khi bị cụt. `/api/chat` không stream vẫn sinh lại 1 lần như v1.
- **Câu bác bỏ cũng bị lược.** Câu nhắc lại khoảng mớm để bác bỏ ("không phải 70–99") cũng bị hậu kiểm lược, vì khoảng đó không có trong nguồn. Câu đúng ở phía sau vẫn được giữ.
- **Gắn tên cơ quan khi so sánh** (RG-18/19) phụ thuộc vào LLM, chưa có kiểm tất định.

## 5. Việc còn lại để đóng REQ

1. Boss chạy server phụ :8002 với code mới, Atlas chạy `--runs 3` rồi điền các cột "sau" ở mục 3.1:
   ```
   cd ~/DaiHoc/Nam4/LTHTTM/project && docker run -d --name da03-api --network project_default --env-file .env -p 127.0.0.1:8002:8000 -v $PWD/artifacts:/app/artifacts -v $PWD/data:/app/data -v ../wt-da03-t1/knowledge:/app/knowledge -v ../wt-da03-t1/ml:/app/ml -v ../wt-da03-t1/backend:/app/backend project-api:latest
   ```
2. Hawk kiểm độc lập: guard bằng bộ đối chiếu riêng, K-01 frontend, đo lại NFR-1.
3. Boss commit hoặc stash các sửa dở trên `feature/dataset-kb-upgrade` (chuỗi "multi agent", tên PDF, cổng 7687), rồi tự merge `req-da-03/t1-t3`.
