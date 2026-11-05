# Đường An — demo hệ đa Agent hỗ trợ thông tin tiểu đường

**Trạng thái:** mã nền để phát triển và nghiên cứu, chưa phải sản phẩm y tế. Các mô hình chỉ hoạt động sau khi đã huấn luyện; RAG chỉ hoạt động sau khi nạp tài liệu và khởi động Neo4j/Ollama. Xem [ANTIGRAVITY_TASKS.md](ANTIGRAVITY_TASKS.md) để biết các việc còn lại và tiêu chí nghiệm thu.

## Địa chỉ và tài liệu dự án

- Website demo được cấu hình: [diabetes.handq2212.site](https://diabetes.handq2212.site). Ngày 05/11/2026, yêu cầu kiểm tra tự động nhận HTTP 403 từ Cloudflare; chưa xác nhận truy cập công khai bằng trình duyệt. Website phụ thuộc máy chủ cá nhân và tunnel, không phải dịch vụ luôn sẵn sàng.
- Mã nguồn GitHub: [HandQ2212/project-agent-diabets](https://github.com/HandQ2212/project-agent-diabets).
- [Báo cáo PDF](bao_cao_project/Bao_cao_Duong_An.pdf), [mã nguồn báo cáo](bao_cao_project/Bao_cao_Duong_An.tex) và [notebook huấn luyện](notebooks/training/README.md).

Không nhập dữ liệu sức khỏe thật hoặc thông tin nhận dạng. Phân loại không phải chẩn đoán; không sử dụng ứng dụng để đưa ra quyết định điều trị.

## Chạy demo trên macOS Apple Silicon

Yêu cầu: Docker Desktop đang chạy, Ollama cài trên máy, đủ dung lượng cho image, dữ liệu và mô hình. Ollama chạy trên host để dùng GPU Apple Silicon; các container kết nối qua `host.docker.internal`. Node chỉ cần khi phát triển frontend ngoài Docker.

1. Tải Ollama từ <https://ollama.com/download>, khởi động dịch vụ; tải mô hình:
   ```sh
   ollama pull qwen3:4b-instruct
   ollama pull nomic-embed-text
   ```
2. Nếu chưa có `.env`, sao chép cấu hình: `cp .env.example .env`. Thay các mật khẩu mẫu trong `.env` nhất quán giữa `NEO4J_AUTH`/`NEO4J_PASSWORD` và `MYSQL_PASSWORD`/`DATABASE_URL`; không đưa tệp này lên Git. Giữ `STORE_DEMO_HISTORY=false` nếu không muốn lưu sự kiện.
3. Chạy `docker compose up --build -d`. Truy cập <http://localhost:8080>, API docs <http://localhost:8001/docs>. Có thể đổi cổng API qua biến `API_HOST_PORT`. Lần đầu tải image và cài thư viện có thể mất thời gian.
4. Nạp tri thức demo: `docker compose exec api python -m ml.seed_knowledge`.
5. Các snapshot mô hình phục vụ demo và kết quả thí nghiệm đã chọn nằm trong `artifacts/`. Muốn huấn luyện lại, tải và chuẩn bị dữ liệu theo [docs/DATA.md](docs/DATA.md), rồi chạy:
   ```sh
   docker compose exec api python -m ml.train symptoms data/raw/diabetes_data_upload.csv
   docker compose exec api python -m ml.train brfss data/raw/LLCP2021.XPT data/raw/LLCP2022.XPT data/raw/LLCP2023.XPT
   docker compose exec api python -m ml.rl
   ```
   Các tệp mô hình, tiền xử lý và báo cáo nằm trong `artifacts/`; huấn luyện có thể mất nhiều thời gian. Artifact tạo bằng Python/thư viện khác môi trường Docker có thể không tương thích; hãy huấn luyện lại trong container trước khi demo. Chỉ tải artifact do bạn tạo hoặc nguồn tin cậy.
6. Mở giao diện, chọn biểu mẫu hoặc hỏi đáp. Nếu chưa huấn luyện/nạp tri thức, API báo trạng thái chưa sẵn sàng; không có dự đoán mẫu tự tạo.

`docker compose down` dừng hệ thống, không xóa volume. MySQL chỉ lưu thời điểm và loại sự kiện nếu bật `STORE_DEMO_HISTORY=true`, không lưu câu hỏi, chỉ số hay câu trả lời.

## Giới hạn quan trọng

- Có thêm biểu mẫu NHANES **chỉ dành cho ví dụ giả lập**, dùng CNN 1D và các chỉ số glucose/HbA1c/BMI/tuổi để phân loại nhãn tự khai về chẩn đoán trước đó. Đây không phải dự báo bệnh mới, công cụ sàng lọc hay chẩn đoán; xem [phân tích dữ liệu và kết quả thử nghiệm](docs/EXPERIMENT_CLINICAL.md).
- Website có thêm biểu mẫu NHANES 15 chỉ số dùng snapshot CNN seed 42, bộ tiền xử lý và ngưỡng 0,8 được chọn trong notebook `04_NHANES_15_Chi_So.ipynb`. Snapshot tại `artifacts/nhanes15_web` lấy từ lần chạy `artifacts/notebook_runs/nhanes15/20261105T081930_945286Z`; cả hai được lưu trong Git để tái lập demo. Đây là dữ liệu Hoa Kỳ, không phải WHO hay người Việt Nam; chỉ dùng dữ liệu giả lập.

- Một thí nghiệm NHANES 15 chỉ số trước đó được ghi tại [NHANES15](data/metadata/NHANES15.md); artifact của thí nghiệm này không phải snapshot đang dùng cho website.
- Các notebook tách riêng theo bài toán, từ phân tích dữ liệu đến lựa chọn mô hình, nằm trong [notebooks/training](notebooks/training/README.md). Kết quả huấn luyện notebook được lưu riêng và không tự triển khai lên website.

- BRFSS là khảo sát cắt ngang tự báo cáo; nhãn là từng được báo mắc bệnh, không phải dự báo mắc mới. Hiện pipeline không dùng survey weight; báo cáo đánh giá là không trọng số.
- UCI chỉ 520 mẫu từ một cơ sở; kết quả không được kiểm chứng trên người dùng Việt Nam. Điểm mô hình không phải xác suất chẩn đoán đã hiệu chỉnh.
- Kho tri thức gồm các đoạn tổng hợp ngắn minh họa, bao gồm nguồn Vinmec và Long Châu; các đoạn này chưa được chuyên gia thẩm định độc lập. Cần thẩm định nội dung, bổ sung tài liệu, đánh giá tìm kiếm, phản hồi tiếng Việt, quy tắc và trích dẫn trước demo công khai.
- RL tối ưu phần thưởng giả lập, không chứng minh lợi ích y khoa và không chọn phương pháp điều trị.
- Không xuất bản công khai trước khi hoàn tất kiểm tra bảo mật, hạn chế truy cập, kiểm thử và thẩm định nội dung. Docker Compose không tự thiết lập tunnel.

Nếu cần tạo lại snapshot trong thư mục đích chưa tồn tại, chạy `python -m ml.prepare_nhanes15_web artifacts/notebook_runs/nhanes15/20261105T081930_945286Z`. Lệnh chỉ chấp nhận lần chạy đầy đủ chọn CNN seed 42 với đúng thứ tự đặc trưng; nếu notebook chọn model khác cần cập nhật và kiểm thử API thay vì gắn nhãn sai.

## Kiểm tra và triển khai

Sau khi cài dependency, chạy `python -m pytest backend/tests -q` và `cd frontend && npm ci && npm run build`. Docker chưa được coi là kiểm thử thành công chỉ vì có cấu hình. Các bước Cloudflare/GitHub và danh sách việc chưa hoàn thành nằm trong [ANTIGRAVITY_TASKS.md](ANTIGRAVITY_TASKS.md).
## Cloudflare Tunnel cho máy này

DNS `diabetes.handq2212.site` đã được cấu hình tới tunnel `diabetes-handq2212`. Khóa và cấu hình cục bộ trong `.cloudflared/` là bí mật, không đưa lên Git. Khi Docker Desktop đang chạy, dùng:

```sh
docker compose -f docker-compose.yml -f docker-compose.tunnel.yml up -d --build
```

Tắt toàn bộ dịch vụ và tunnel bằng:

```sh
docker compose -f docker-compose.yml -f docker-compose.tunnel.yml down
```

Tunnel trỏ đến container web trên mạng nội bộ Docker. Website chỉ hoạt động khi máy, Docker Desktop và các dịch vụ đang chạy. Đây là demo công khai chưa thiết lập Cloudflare Access; không nhập thông tin sức khỏe cá nhân. Ollama chạy trên máy chủ và cần được khởi động riêng cho chức năng RAG.

## Thu thập tri thức web theo lịch

Dịch vụ `knowledge-refresh` chỉ chạy thủ công khi cần nạp hoặc cập nhật các trang CDC/NIDDK được liệt kê tại `knowledge/web_sources.json`. Khi có lỗi kết nối dịch vụ hoặc tải nguồn, dữ liệu cũ được giữ lại. Trong lúc chat, hệ thống chỉ truy xuất tri thức đã có trong Neo4j, không thu thập thêm từ web. Chỉ thêm URL HTTPS thuộc danh sách domain được phép trong `ml/refresh_web.py`; chương trình tôn trọng `robots.txt`, kiểm tra chuyển hướng và giới hạn kích thước trang. Neo4j lưu các đoạn nội dung, nguồn, thời gian tải và embedding. Nguồn web được đánh dấu **chưa kiểm duyệt chuyên môn**; không coi trích dẫn là bằng chứng thẩm định y tế. Chỉ thêm nguồn nếu điều kiện sử dụng cho phép xử lý nội dung.

Để cập nhật thủ công và xem log:

```sh
docker compose -f docker-compose.yml -f docker-compose.tunnel.yml --profile ingest run --rm knowledge-refresh
```

Việc tải nguồn, dịch câu hỏi tìm kiếm và câu trả lời đều có thể sai; cần đối chiếu nguồn gốc và kiểm duyệt chuyên môn trước khi sử dụng cho tư vấn sức khỏe. Nếu Ollama hoặc nguồn web không hoạt động, tài liệu đã nạp trước đó vẫn được giữ lại.

Hệ thống không dùng nội dung web tự động chưa được kiểm duyệt để tạo tóm tắt y khoa. Nếu chỉ tìm thấy nguồn web tự động, hệ thống đưa liên kết thay vì tóm tắt; nếu có cả nội dung nhập thủ công, chỉ nội dung nhập thủ công được dùng để tạo câu trả lời. Lý do: kiểm thử thực tế đã phát hiện mô hình có thể dịch sai hoặc bổ sung thông tin không có trong nguồn. Các đoạn tổng hợp thủ công trong `sources.json` vẫn cần được kiểm tra chuyên môn độc lập.

Lịch sử chat chỉ được giữ trong bộ nhớ phiên trình duyệt; tối đa 10 tin nhắn gần nhất được gửi cùng câu hỏi để hiểu ngữ cảnh. Không nhập thông tin sức khỏe hoặc định danh cá nhân thật.

## Hiển thị phản hồi theo luồng

Chat sử dụng HTTP streaming (NDJSON) để hiện từng đoạn Ollama trả về; các phản hồi kiểm tra an toàn vẫn đi qua cùng quy tắc trước khi truy xuất. Cần chạy lại `docker compose up --build -d` để cập nhật API và cấu hình proxy, sau đó chạy `docker compose exec api python -m ml.seed_knowledge` để nạp các đoạn mới. Nguồn thu thập tự động vẫn chỉ hiện liên kết nếu chưa kiểm duyệt. Luồng sinh nội dung không đảm bảo câu trả lời đã được kiểm chứng chuyên môn; khi mất kết nối giao diện báo lỗi và cho phép gửi lại.
