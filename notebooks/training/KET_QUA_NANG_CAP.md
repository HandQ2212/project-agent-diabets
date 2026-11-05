# Kết quả notebook nâng cấp — 05/11/2026

Kết quả từ lần chạy đầy đủ, ba seed; mô hình và ngưỡng được chọn trên validation. Các bộ test từng được xem ở lần chạy trước nên không còn là kiểm định cuối độc lập.

| Notebook | Mô hình chọn theo validation | Kết quả test | Seed / epoch thực tế |
| --- | --- | --- | --- |
| [UCI triệu chứng](01_UCI_Trieu_Chung.ipynb) | neural_seed_42 | AUC 0.9196 (bootstrap 0.8373–0.9777); F1 0.8485; n=51 | 42: 60 (best 35), 43: 60 (best 35), 44: 64 (best 39); [chi tiết](../../artifacts/notebook_runs/symptoms/20261105T081909_132631Z/report.json) |
| [BRFSS khảo sát](02_BRFSS_Khao_Sat.ipynb) | hist_gradient_boosting | AUC 0.7648 (bootstrap 0.7630–0.7663); F1 0.3975; n=418492 | 42: 77 (best 52), 43: 54 (best 29), 44: 84 (best 59); [chi tiết](../../artifacts/notebook_runs/brfss/20261105T082221_854019Z/report.json) |
| [NHANES 4 chỉ số](03_NHANES_4_Chi_So.ipynb) | neural_seed_43 | AUC 0.9491 (bootstrap 0.9357–0.9595); F1 0.7724; n=2408 | 42: 40 (best 13), 43: 42 (best 17), 44: 46 (best 21); [chi tiết](../../artifacts/notebook_runs/nhanes4/20261105T081915_164118Z/report.json) |
| [NHANES 15 chỉ số](04_NHANES_15_Chi_So.ipynb) | neural_seed_42 | AUC 0.9314 (bootstrap 0.9130–0.9487); F1 0.7549; n=2038 | 42: 70 (best 45), 43: 62 (best 37), 44: 56 (best 31); [chi tiết](../../artifacts/notebook_runs/nhanes15/20261105T081930_945286Z/report.json) |
| [Assignment 02](05_Assignment02_HbA1c_Gia_Lap.ipynb) | logistic_regression | AUC 0.9231 (bootstrap 0.8657–0.9705); F1 0.6364; n=78 | 42: 41 (best 16), 43: 42 (best 17), 44: 48 (best 23); [chi tiết](../../artifacts/notebook_runs/assignment02/20261105T081957_475312Z/report.json) |
| [DQN giáo dục](06_DQN_Giao_Duc.ipynb) | greedy | reward 2.0260 | 42: 30000 bước (best 5000), 43: 30000 bước (best 5000), 44: 30000 bước (best 5000); [chi tiết](../../artifacts/notebook_runs/rl_education/20261105T082005_333033Z/report.json) |

Bootstrap phân tầng chỉ phản ánh bất định điều kiện theo mẫu test, chưa tính thiết kế khảo sát. Các seed chỉ thay đổi khởi tạo, không thay thế nhiều phép chia dữ liệu hay kiểm định ngoài. Nhãn UCI và BRFSS/NHANES khác mục đích; assignment 02 dùng nhãn nhân tạo HbA1c; DQN là mô phỏng. Không dùng các model này để chẩn đoán/sàng lọc hoặc suy rộng sang người Việt Nam.

Sáu thư mục artifact của các lần chạy đầy đủ trong bảng và các lần chạy được trích dẫn trong bảng kết quả lịch sử được lưu trong Git; các lần chạy khác bị bỏ qua. Notebook chứa kết quả và đồ thị đã lưu. Các lần chạy không tự thay đổi mô hình website; snapshot NHANES 15 được sao chép riêng sau khi lựa chọn.
