# Kết quả phiên bản notebook đầu tiên — 05/11/2026

**Lưu trữ lịch sử:** bảng này thuộc phiên bản notebook trước khi mở rộng thực nghiệm; không dùng làm kết quả của phiên bản notebook hiện tại.

Sáu notebook đã chạy đầy đủ trong container Python 3.11; đầu ra và biểu đồ được lưu trực tiếp trong từng notebook. Mỗi mô hình được chọn theo validation; các chỉ số dưới đây thuộc tập test của mô hình được chọn. Các kết quả không so sánh trực tiếp giữa những bộ dữ liệu khác nhau.

| Bài toán | Mô hình/chính sách được chọn | Kết quả test | Báo cáo chi tiết |
| --- | --- | --- | --- |
| [UCI triệu chứng](01_UCI_Trieu_Chung.ipynb) | neural_network | ROC-AUC 0.9232; precision 1.0000; recall 0.7143; n=51 | [report.json](../../artifacts/notebook_runs/symptoms/20261105T080707_170181Z/report.json) |
| [BRFSS khảo sát](02_BRFSS_Khao_Sat.ipynb) | neural_network | ROC-AUC 0.7644; precision 0.2556; recall 0.7567; n=418492 | [report.json](../../artifacts/notebook_runs/brfss/20261105T080820_391496Z/report.json) |
| [NHANES 4 chỉ số](03_NHANES_4_Chi_So.ipynb) | neural_network | ROC-AUC 0.9475; precision 0.6248; recall 0.8840; n=2408 | [report.json](../../artifacts/notebook_runs/nhanes4/20261105T080727_380462Z/report.json) |
| [NHANES 15 chỉ số](04_NHANES_15_Chi_So.ipynb) | logistic_regression | ROC-AUC 0.9359; precision 0.5363; recall 0.8623; n=2038 | [report.json](../../artifacts/notebook_runs/nhanes15/20261105T080734_600184Z/report.json) |
| [Assignment 02](05_Assignment02_HbA1c_Gia_Lap.ipynb) | logistic_regression | ROC-AUC 0.9002; precision 0.6471; recall 0.8462; n=77 | [report.json](../../artifacts/notebook_runs/assignment02/20261105T080743_154326Z/report.json) |
| [DQN giáo dục](06_DQN_Giao_Duc.ipynb) | greedy | Reward trung bình 2.0260; 200 episode/seed | [report.json](../../artifacts/notebook_runs/rl_education/20261105T080750_006650Z/report.json) |

BRFSS và NHANES là dữ liệu Hoa Kỳ; UCI là dữ liệu Bangladesh; assignment 02 dùng nhãn tạo từ HbA1c. DQN chỉ là môi trường giả lập. Các kết quả không phải chẩn đoán hoặc dự báo bệnh mới và không chứng minh hiệu quả trên người Việt Nam.

Artifact và báo cáo của các lần chạy trong bảng được lưu trong Git để tham khảo lịch sử. Notebook chứa đầu ra đã chạy nhưng không thay thế các model website.
