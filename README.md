# Đường An — demo hệ đa Agent hỗ trợ thông tin tiểu đường

**Trạng thái:** mã nền để phát triển và nghiên cứu, chưa phải sản phẩm y tế. Các mô hình chỉ hoạt động sau khi đã huấn luyện; RAG chỉ hoạt động sau khi nạp tài liệu và khởi động Neo4j/Ollama. Xem [ANTIGRAVITY_TASKS.md](ANTIGRAVITY_TASKS.md) để biết các việc còn lại và tiêu chí nghiệm thu.

Không nhập dữ liệu sức khỏe thật hoặc thông tin nhận dạng. Phân loại không phải chẩn đoán; không sử dụng ứng dụng để đưa ra quyết định điều trị.

## Chạy demo trên macOS Apple Silicon

Yêu cầu: Docker Desktop đang chạy, Ollama cài trên máy, đủ dung lượng cho image, dữ liệu và mô hình. Ollama chạy trên host để dùng GPU Apple Silicon; các container kết nối qua `host.docker.internal`. Node chỉ cần khi phát triển frontend ngoài Docker.

1. Tải Ollama từ <https://ollama.com/download>, khởi động dịch vụ; tải mô hình:
   ```sh
   ollama pull qwen3:4b-instruct
   ollama pull nomic-embed-text
   ```
2. Nếu chưa có `.env`, sao chép cấu hình: `cp .env.example .env`. Thay các mật khẩu mẫu trong `.env` nhất quán giữa `NEO4J_AUTH`/`NEO4J_PASSWORD` và `MYSQL_PASSWORD`/`DATABASE_URL`; không đưa tệp này lên Git. Giữ `STORE_DEMO_HISTORY=false` nếu không muốn lưu sự kiện.
3. Chạy `docker compose up --build -d`. Truy cập <http://localhost:8080>, API docs <http://localhost:8000/docs>. Lần đầu tải image và cài thư viện có thể mất thời gian.
4. Nạp tri thức demo: `docker compose exec api python -m ml.seed_knowledge`.
5. Tải và chuẩn bị dữ liệu theo [docs/DATA.md](docs/DATA.md), rồi huấn luyện:
   ```sh
   docker compose exec api python -m ml.train symptoms data/raw/diabetes_data_upload.csv
   docker compose exec api python -m ml.train brfss data/raw/LLCP2021.XPT data/raw/LLCP2022.XPT data/raw/LLCP2023.XPT
   docker compose exec api python -m ml.rl
   ```
   Các tệp mô hình, tiền xử lý và báo cáo nằm trong `artifacts/`; huấn luyện có thể mất nhiều thời gian. Artifact tạo bằng Python/thư viện khác môi trường Docker có thể không tương thích; hãy huấn luyện lại trong container trước khi demo. Chỉ tải artifact do bạn tạo hoặc nguồn tin cậy.
6. Mở giao diện, chọn biểu mẫu hoặc hỏi đáp. Nếu chưa huấn luyện/nạp tri thức, API báo trạng thái chưa sẵn sàng; không có dự đoán mẫu tự tạo.

`docker compose down` dừng hệ thống, không xóa volume. MySQL chỉ lưu thời điểm và loại sự kiện nếu bật `STORE_DEMO_HISTORY=true`, không lưu câu hỏi, chỉ số hay câu trả lời.

## Giới hạn quan trọng

- BRFSS là khảo sát cắt ngang tự báo cáo; nhãn là từng được báo mắc bệnh, không phải dự báo mắc mới. Hiện pipeline không dùng survey weight; báo cáo đánh giá là không trọng số.
- UCI chỉ 520 mẫu từ một cơ sở; kết quả không được kiểm chứng trên người dùng Việt Nam. Điểm mô hình không phải xác suất chẩn đoán đã hiệu chỉnh.
- Kho tri thức hiện chỉ có ba đoạn ngắn minh họa. Cần thẩm định nội dung, bổ sung tài liệu, đánh giá tìm kiếm, phản hồi tiếng Việt, quy tắc và trích dẫn trước demo công khai.
- RL tối ưu phần thưởng giả lập, không chứng minh lợi ích y khoa và không chọn phương pháp điều trị.
- Không xuất bản công khai trước khi hoàn tất kiểm tra bảo mật, hạn chế truy cập, kiểm thử và thẩm định nội dung. Docker Compose không tự thiết lập tunnel.

## Kiểm tra và triển khai

Sau khi cài dependency, chạy `python -m pytest backend/tests -q` và `cd frontend && npm ci && npm run build`. Docker chưa được coi là kiểm thử thành công chỉ vì có cấu hình. Các bước Cloudflare/GitHub và danh sách việc chưa hoàn thành nằm trong [ANTIGRAVITY_TASKS.md](ANTIGRAVITY_TASKS.md).
