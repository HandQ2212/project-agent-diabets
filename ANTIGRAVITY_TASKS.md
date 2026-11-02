# Giao việc cho Antigravity — Đường An

## Bối cảnh và quy tắc

Đây là project học thuật về hệ đa Agent cho bệnh tiểu đường, triển khai trên MacBook Pro M1 Pro. Đọc `README.md`, `docs/DATA.md` và mã nguồn trước khi thay đổi. Giao diện tiếng Việt, dự đoán chỉ để học tập, không kê thuốc/điều chỉnh điều trị, không sử dụng dữ liệu thật có thể nhận dạng. Không tự tạo kết quả huấn luyện, nguồn trích dẫn, thông số đánh giá hoặc báo đã deploy khi chưa có bằng chứng. Không commit dữ liệu thô, secrets, artifact không được phép hoặc dữ liệu người dùng.

## 1. Môi trường và dữ liệu

- Khởi động Docker Desktop, cài Ollama host, tải `qwen3:4b-instruct` và `nomic-embed-text`; kiểm tra RAM, thời gian khởi động và tốc độ phản hồi khi tất cả dịch vụ chạy. Chọn model nhỏ hơn nếu máy thiếu bộ nhớ; ghi rõ phép đo và RAM máy.
- Tải BRFSS 2021, 2022, 2023 dạng SAS XPT và codebook từ CDC; kiểm tra toàn bộ biến, mã giá trị và phiên bản theo từng năm. Tải UCI Early Stage từ nguồn chính thức. Ghi nguồn, giấy phép, số dòng gốc/được giữ/loại và phân bố lớp.
- Chạy hai pipeline ở README. Sửa mọi vấn đề tương thích dữ liệu thực tế và kiểm tra các phép chia, preprocessing, rò rỉ nhãn, missing values. Giữ 2023 làm test BRFSS, train/validation chỉ dùng 2021–22; không đưa test vào tuning. Giải thích hạn chế khảo sát cắt ngang và việc không dùng trọng số; không diễn giải là dự đoán bệnh tương lai.
- Kiểm tra và lưu báo cáo neural network so với logistic regression với confusion matrix, precision, recall, F1, ROC-AUC và phân bố nhãn. Đánh giá ngưỡng/phân lớp và hiệu chỉnh điểm; phân tích sai lệch theo nhóm nếu đủ dữ liệu. Không kết luận hiệu năng cho Việt Nam hoặc sử dụng y tế.

## 2. Knowledge Base, RAG và hệ đa Agent

- Kho hiện chỉ có ba đoạn minh họa. Bổ sung tài liệu chính thức có nguồn, kiểm tra quyền sử dụng và nội dung, ngày, URL; chuẩn hóa, chia đoạn, tạo quan hệ Neo4j và embedding, nạp có thể chạy lại. Đảm bảo trích dẫn thực sự hỗ trợ các phát biểu.
- Xây tập câu hỏi tiếng Việt có đáp án và nguồn kiểm chứng; đánh giá chất lượng truy xuất, hallucination, trích dẫn, trường hợp không có nguồn, tiếng Việt và dịch vụ lỗi. Điều chỉnh embedding đa ngôn ngữ nếu cần. Không bịa câu trả lời khi không có tài liệu.
- Hoàn thiện Rule Agent: phát hiện tình huống khẩn cấp, yêu cầu thuốc/liều/điều trị và dữ liệu nhạy cảm; phản hồi an toàn phù hợp. Không coi lọc từ khóa hiện tại là cơ chế an toàn đầy đủ. Kiểm tra prompt injection trong tài liệu và câu hỏi.
- Mở rộng điều phối để Prediction, Knowledge, Rule, Learning và Response là các bước có hợp đồng, nhiệm vụ rõ ràng; hiện chat dùng LangGraph còn prediction/RL được gọi riêng. Hiển thị trace thực tế; tránh mô tả chức năng chưa triển khai.

## 3. Reinforcement Learning

- Chạy `python -m ml.rl`, kiểm tra chính sách DQN được lưu và báo cáo so sánh random trên seed đánh giá tách biệt. Giải thích đầy đủ state, action, reward, episode và rủi ro mô phỏng; bổ sung baseline có ý nghĩa và kiểm tra nhiều seed.
- Đảm bảo trạng thái toàn số 0 có hành vi phù hợp, không chọn chủ đề đã hoàn tất khi còn chủ đề cần học; nếu chính sách không đạt tiêu chí, báo rõ thay vì tự kết luận thành công. Không dùng RL cho điều trị hoặc gán tác động y tế cho phần thưởng mô phỏng.

## 4. Giao diện, dữ liệu ứng dụng và bảo mật

- Cài dependency, build React/TypeScript, kiểm thử biểu mẫu và responsive; bổ sung giao diện hiển thị điểm, loại dữ liệu, giới hạn và trạng thái dịch vụ. Kiểm tra chính xác nhóm tuổi BRFSS 18–24, 25–29…80+ và mô tả các biến.
- MySQL hiện chỉ hỗ trợ log loại sự kiện nếu bật tùy chọn, không chứa hồ sơ y tế. Chỉ bổ sung lịch sử chi tiết nếu có yêu cầu, thiết kế sự đồng ý, xác thực, phân quyền, thời hạn lưu và xóa dữ liệu. Không lưu dữ liệu thật trong demo.
- Kiểm thử RAG, đầu vào sai, thiếu artifact, Neo4j/Ollama mất kết nối, không tìm thấy nguồn và RL chưa huấn luyện. Thêm rate limit, xác thực truy cập demo, bảo vệ secret, kiểm tra dependency trước khi cho phép truy cập Internet.

## 5. GitHub, subdomain và báo cáo

- Tạo repository Git, kiểm tra `.gitignore` và quét bí mật; tạo remote GitHub theo tài khoản và quyền được cấp, push mã nguồn. Không tự tạo bằng chứng push.
- Sau khi kiểm tra an toàn cho demo, thiết lập Cloudflare Tunnel tới `http://localhost:8080` trên máy chạy dịch vụ; trỏ `diabetes.handq2212.site` theo [hướng dẫn Cloudflare](https://developers.cloudflare.com/tunnel/get-started/). Chỉ thiết lập sau khi xác nhận quyền zone, tài khoản và cấu hình DNS hiện tại; không thay đổi bản ghi không liên quan. Giữ tunnel token ngoài Git. Dùng Cloudflare Access để hạn chế người xem demo. Kiểm tra HTTPS, hoạt động sau restart và lưu ý máy phải luôn bật.
- Viết báo cáo: giới thiệu, hệ đa Agent, kiến trúc, dữ liệu, Deep Learning và đánh giá, KB/RAG, RL, code và demo; ghi kết quả đo thực tế, nguồn, giới hạn và việc còn thiếu. Có sơ đồ và kịch bản demo tái lập.

## Tiêu chí hoàn thành

1. Hai mô hình được huấn luyện thật, artifacts và báo cáo có nguồn dữ liệu; hai biểu mẫu hoạt động từ đầu đến cuối.
2. RAG truy xuất nguồn thật, nêu khi không đủ nguồn; quy tắc an toàn và các lỗi dịch vụ được kiểm thử.
3. RL huấn luyện thật, có báo cáo so sánh với baseline mô phỏng; không tạo khuyến nghị điều trị.
4. Test backend, frontend build, Docker Compose, kiểm tra giao diện trên điện thoại/máy tính và benchmark M1 Pro đều có kết quả ghi lại.
5. Có GitHub URL, HTTPS subdomain hoạt động, kiểm soát truy cập phù hợp và báo cáo. Nếu thiếu tài khoản, dữ liệu, Docker hoặc mạng, nêu chính xác việc bị chặn và lệnh tiếp tục.
