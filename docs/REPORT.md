# Báo cáo demo — bản nháp đang phát triển

## 1. Mục tiêu và giới hạn

Hệ thống học thuật hỗ trợ tìm hiểu thông tin về tiểu đường bằng hai mô hình phân loại dữ liệu bảng, kho tri thức Neo4j, RAG, các Agent và mô phỏng học tăng cường. Không dùng để chẩn đoán hoặc điều trị.

## 2. Kiến trúc

Giao diện React gửi yêu cầu đến FastAPI. Prediction API nạp mô hình PyTorch và bộ tiền xử lý tương ứng. Đối với hỏi đáp, đồ thị LangGraph gọi Rule Agent → Knowledge Agent (Neo4j + embedding Ollama) → Response Agent (Ollama). RL được gọi qua endpoint mô phỏng riêng. MySQL chỉ ghi sự kiện không chứa dữ liệu sức khỏe khi được bật.

## 3. Dữ liệu và mô hình triệu chứng

Nguồn [UCI Early Stage Diabetes Risk Prediction](https://archive.ics.uci.edu/dataset/529/early%2Bstage%2Bdiabetes%2Brisk%2Bprediction%2Bdataset), CC BY 4.0; 520 dòng, 251 hồ sơ duy nhất sau loại 269 dòng trùng, không có xung đột nhãn theo bộ đặc trưng. Các hồ sơ duy nhất được chia train 160, validation 40, test 51; seed 42. Mô hình MLP hai lớp ẩn so với logistic regression cân bằng lớp, tiền xử lý fit trên train.

Một lần chạy cục bộ: neural network ROC-AUC 0,923, recall lớp dương tính 0,714, F1 lớp dương tính 0,833; confusion matrix `[[16, 0], [10, 25]]`. Logistic regression ROC-AUC 0,912, recall dương tính 0,771, F1 dương tính 0,857; confusion matrix `[[15, 1], [8, 27]]`. Chi tiết: `artifacts/symptoms/report.json` trên máy đã chạy. Tập test rất nhỏ và cùng nguồn với train, nên các số này chỉ minh họa, không chứng minh tính phù hợp lâm sàng. Artifact tạo trên máy cần được huấn luyện lại nếu không tương thích môi trường Docker.

## 4. Dữ liệu BRFSS và mô hình sức khỏe

Dùng tệp khảo sát CDC 2021–2023, 2021–22 để phát triển và 2023 để kiểm thử. `_RFHYPE6` không có trong tệp 2022 và đã loại khỏi cả ba năm. Xem `docs/DATA.md` để biết biến, định nghĩa nhãn và các giới hạn. Sau lọc nhãn: 423.958 bản ghi năm 2021, 429.880 năm 2022 và 418.492 năm 2023. Tập train có 683.070 mẫu, validation 170.768 và test 418.492; tỷ lệ dương tính ở test khoảng 14,29%. Một lần chạy cục bộ: MLP có ROC-AUC 0,7643, recall dương tính 0,7525, F1 dương tính 0,3840 và confusion matrix `[[229158, 129548], [14798, 44988]]`. Logistic regression có ROC-AUC 0,7618, recall dương tính 0,7533 và F1 dương tính 0,3823. Chi tiết nằm trong `artifacts/brfss/report.json`. Đây là khảo sát tự báo cáo, chỉ số không trọng số và không phải đánh giá lâm sàng.

## 5. Knowledge Base và RAG

Kho hiện chứa ba đoạn tri thức minh họa có URL; embedding dùng Ollama và truy xuất cosine từ Neo4j. Chưa đánh giá chất lượng tiếng Việt, khả năng chống prompt injection hay độ chính xác của các trích dẫn. Cần kiểm tra và mở rộng trước demo công khai.

## 6. Mô phỏng Reinforcement Learning

Trạng thái là bốn giá trị nhị phân biểu thị chủ đề chưa hoàn thành; hành động chọn một trong bốn chủ đề; phần thưởng +1 nếu chủ đề còn cần và -0,25 nếu không. Mỗi episode bốn lượt. DQN được huấn luyện 30.000 bước, kiểm tra 200 episode trên seed khác; một lần chạy cho mean reward 1,2625 so với 0,58125 của chọn ngẫu nhiên. Đây là phần thưởng do người thiết kế đặt ra, không phản ánh kết quả sức khỏe hay hiệu quả thực tế. Chi tiết: `artifacts/rl/report.json`.

## 7. Việc cần hoàn thành

Kiểm thử tích hợp Docker/Neo4j/Ollama trên M1 Pro, kiểm chứng tri thức và an toàn, kiểm tra mobile/desktop, bổ sung bảo mật, báo cáo dataset và kết quả BRFSS, cấu hình GitHub và HTTPS. Xem `ANTIGRAVITY_TASKS.md` để tiếp tục.
