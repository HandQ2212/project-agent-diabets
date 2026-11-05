# Notebook huấn luyện theo từng bài toán

Mở notebook trong VS Code/Jupyter và chạy các cell lần lượt từ trên xuống. Mỗi notebook chứa mã đọc/biểu diễn dữ liệu, làm sạch, chia tập, huấn luyện, đánh giá và lựa chọn mô hình. Các notebook dùng dữ liệu và môi trường của dự án; không tự thay thế model đang phục vụ website.

Kết quả notebook nâng cấp được tổng hợp trong [KET_QUA_NANG_CAP.md](KET_QUA_NANG_CAP.md); từng notebook lưu đầu ra và biểu đồ. [KET_QUA_CHAY.md](KET_QUA_CHAY.md) là kết quả phiên bản cũ.

| Notebook | Dữ liệu, mục đích | Mô hình được so sánh |
| --- | --- | --- |
| [01_UCI_Trieu_Chung.ipynb](01_UCI_Trieu_Chung.ipynb) | UCI Bangladesh: phân loại nhãn từ triệu chứng | MLP và Logistic Regression |
| [02_BRFSS_Khao_Sat.ipynb](02_BRFSS_Khao_Sat.ipynb) | BRFSS Hoa Kỳ: phân loại trạng thái tự báo cáo từng được thông báo mắc bệnh | MLP và Logistic Regression |
| [03_NHANES_4_Chi_So.ipynb](03_NHANES_4_Chi_So.ipynb) | NHANES Hoa Kỳ: nhãn tự khai, 4 biến | CNN 1D và Logistic Regression |
| [04_NHANES_15_Chi_So.ipynb](04_NHANES_15_Chi_So.ipynb) | NHANES Hoa Kỳ: nhãn tự khai, 15 biến | CNN 1D và Logistic Regression |
| [05_Assignment02_HbA1c_Gia_Lap.ipynb](05_Assignment02_HbA1c_Gia_Lap.ipynb) | Assignment 02: nhãn tạo từ `glyhb > 6.5`; không cho `glyhb` vào đầu vào | CNN 1D và Logistic Regression |
| [06_DQN_Giao_Duc.ipynb](06_DQN_Giao_Duc.ipynb) | Môi trường giả lập chọn chủ đề giáo dục | DQN, greedy và random |

Các bài toán phân loại so sánh Dummy, Logistic Regression, HistGradientBoosting và mạng nơ-ron chạy ba seed. Mạng chạy tối đa 200 epoch, tối thiểu 40 epoch và dừng sớm sau 25 epoch không cải thiện validation loss; biểu đồ ghi rõ loss train/validation, epoch tốt nhất và số lần cập nhật. Batch lớn hơn ở BRFSS nên số epoch giữa bài toán không tương đương số lần cập nhật. Ba seed chỉ đo nhạy cảm khởi tạo, không chứng minh độ ổn định theo các tập chia khác nhau.

Mô hình được chọn theo ROC-AUC validation, ngưỡng được chọn theo F1 validation, sau đó chỉ đánh giá ứng viên được chọn trên test. DQN kiểm tra nhiều checkpoint/seed và chọn chính sách theo reward validation, ưu tiên greedy khi bằng nhau, với seed test khác. Đây là quy trình thí nghiệm, không chứng minh giá trị lâm sàng; điểm sigmoid có thể chưa được hiệu chỉnh. Các tập test đã từng được xem trong các lần chạy trước, nên không còn là bằng chứng kiểm định cuối hoàn toàn độc lập.

## Chuẩn bị

1. Cài môi trường Python 3.11, `requirements.txt`, cùng `jupyter`/`ipykernel`. Notebook có đồ thị dùng `matplotlib`.
2. Chuẩn bị dữ liệu UCI và BRFSS theo [docs/DATA.md](../../docs/DATA.md); chuẩn bị NHANES theo [NHANES15.md](../../data/metadata/NHANES15.md). Notebook assignment 02 đọc `data/raw/assignment02_diabetes.csv`, sao chép từ assignment cũ nếu có và kiểm tra nguồn/đơn vị.
3. Chạy notebook mong muốn từ đầu. BRFSS có ba file XPT lớn, cần đủ RAM, dung lượng và thời gian. Với DQN, trạng thái được tạo bằng mô phỏng; không cần bộ dữ liệu người bệnh.

Các lần chạy thường tạo thư mục riêng trong `artifacts/notebook_runs/<bài_toán>/<thời_điểm>/`, gồm báo cáo JSON, thông tin lựa chọn và các mô hình. Các lần chạy được trích dẫn trong hai bảng kết quả được lưu trong Git; các lần chạy mới mặc định bị bỏ qua. Để kiểm thử kỹ thuật nhanh có thể đặt `NOTEBOOK_SMOKE=1`: dữ liệu BRFSS được giới hạn dòng, số epoch/bước giảm và kết quả nằm trong `/tmp/duongan_notebook_smoke`; **không sử dụng kết quả này để báo cáo chất lượng mô hình**.

Notebook cũ ở `notebooks/NHANES_15_Chi_So.ipynb` và `bao_cao_project/notebook/Training_Duong_An.ipynb` được giữ lại làm tham khảo lịch sử; dùng các notebook trong thư mục này cho quy trình lựa chọn mô hình mới. Những notebook mới không tự tái tạo đúng artifact website trước đó, vì chúng chọn mô hình theo validation và lưu riêng.

Các tập NHANES/BRFSS là dữ liệu Hoa Kỳ, không phải WHO STEPS hay người Việt Nam. Các nhãn tự khai hoặc tạo từ ngưỡng xét nghiệm có giới hạn; dữ liệu cắt ngang không dự báo mắc mới. Không dùng model cho chẩn đoán, sàng lọc hoặc điều trị.
