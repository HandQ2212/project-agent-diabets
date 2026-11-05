# Thử nghiệm Deep Learning với các chỉ số đo

## Đối chiếu assignment

- Assignment 02 có `data/diabetes.csv` gồm 403 bản ghi, các cột `stab.glu`, `glyhb`, cholesterol, tuổi và kích thước cơ thể. Chưa có nhãn chẩn đoán độc lập trong tệp đó; nguồn gốc, đơn vị và điều kiện đo cần xác minh trước khi dùng ngoài thử nghiệm.
- Assignment 07 tạo `Outcome = (glyhb > 6.5)` từ cùng dữ liệu. Nếu đưa `glyhb` vào đầu vào khi dự đoán Outcome, mô hình sẽ học lại quy tắc tạo nhãn. Kết quả không chứng minh khả năng nhận biết bệnh.
- Assignment 04 dùng CNN 1D PyTorch với hai lớp Conv1d 16/32 kênh, ReLU, MaxPool, Dense 32, dropout và đầu ra logit. Thử nghiệm dưới đây dùng cùng cấu trúc cơ bản, điều chỉnh độ dài vector về 4. Ảnh yêu cầu của thầy nêu Deep Learning, dự toán/phân loại, KB/RAG và agent, nhưng không xác định riêng CNN là kiến trúc bắt buộc. Tích chập trên thứ tự cột bảng là một giả định thực nghiệm, không có ý nghĩa không gian tự nhiên.

## Thử nghiệm NHANES có nhãn khảo sát

Chạy `docker compose exec api python -m ml.train_nhanes`. Mã tải các tệp XPT công khai từ CDC, ghép theo SEQN: DEMO (tuổi), BMX (BMI), GLU (glucose huyết tương lúc đói, mg/dL), GHB (HbA1c, %) và DIQ (câu trả lời về chẩn đoán trước đó). Các tệp được lưu trong `data/raw/nhanes`, hash SHA-256 và thống kê lưu trong `artifacts/nhanes_research/report.json`. Mô hình và scaler nằm cùng thư mục đó, tách khỏi artifact cũ.

Nhãn DIQ010 là người tham gia trả lời từng được nhân viên y tế thông báo mắc đái tháo đường (1) hoặc không (2); loại câu trả lời tiền đái tháo đường/không rõ, người dưới 18 tuổi và bản ghi thiếu một trong bốn biến. Các chỉ số cùng thời điểm có thể đã chịu ảnh hưởng điều trị; glucose và HbA1c cũng có thể đã được dùng để chẩn đoán trước đó. Đây là phân loại hồi cứu câu trả lời khảo sát, **không phải dự báo khởi phát, sàng lọc hoặc chẩn đoán**.

Chu kỳ 2015–2016 được chia train/validation phân tầng 80/20, scaler fit duy nhất trên train; 2017–2018 là tập test theo chu kỳ. Không khẳng định hai chu kỳ độc lập về mọi người tham gia. Chỉ xét người có đủ dữ liệu thuộc phân mẫu xét nghiệm lúc đói; không dùng trọng số hoặc thiết kế khảo sát, nên kết quả không phải ước lượng đại diện dân số. Không có kiểm định lâm sàng hoặc kiểm định trên người Việt Nam. Điểm sigmoid dùng trọng số lớp không phải xác suất đã hiệu chỉnh. API/giao diện chỉ để chạy ví dụ giả lập, không nhập chỉ số thật.

Lần chạy seed 42: 2.485 bản ghi đủ dữ liệu ở chu kỳ train (1.988 train, 497 validation) và 2.408 ở test (405 nhãn 1). CNN ROC-AUC 0,949, precision 0,612, recall 0,891 tại ngưỡng 0,5; ma trận [[1774, 229], [44, 361]]. Logistic Regression cân bằng lớp đạt ROC-AUC 0,942, precision 0,628, recall 0,872. So sánh này không chứng minh CNN ưu việt hay có giá trị lâm sàng; test chỉ đo cùng nguồn khảo sát ở chu kỳ khác.

## Thử nghiệm bộ assignment 02

Sao chép tệp gốc vào `data/raw/assignment02_diabetes.csv`, rồi chạy `docker compose exec api python -m ml.train_assignment02`. Đây là thử nghiệm độc lập, không đưa ra giao diện. Mã dùng tuổi, BMI tính từ inch/pound, `stab.glu`, `chol`; loại `glyhb`, ID và Outcome khỏi đầu vào, chỉ dùng `glyhb > 6.5` để tái tạo nhãn của assignment 07. BMI và đơn vị vẫn cần xác minh theo nguồn gốc. Loại bản ghi thiếu glyhb thay vì gán nhãn âm.

Với seed 42 có 383 bản ghi đủ dữ liệu, chia 244/62/77 train/validation/test; CNN ROC-AUC 0,921 và F1 0,710, Logistic Regression ROC-AUC 0,900 và F1 0,733. Test chỉ có 13 mẫu nhãn 1; kết quả dao động lớn và không đại diện đánh giá chẩn đoán. Báo cáo JSON lưu trong `artifacts/assignment02_research`; không có nhãn bệnh độc lập, nên không dùng mô hình này để dự đoán bệnh.

Nguồn CDC: [DIQ 2017–2018](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/DIQ_J.htm), [glucose](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/GLU_J.htm), [HbA1c](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/GHB_J.htm), [chỉ số cơ thể](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/BMX_J.htm). Cần đối chiếu codebook tương ứng của từng chu kỳ khi thay đổi biến hoặc tập dữ liệu.
