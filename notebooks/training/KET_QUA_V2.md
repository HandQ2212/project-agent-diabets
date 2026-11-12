# Kết quả nâng cấp dữ liệu — 12/11/2026

Chạy đầy đủ, ba seed mạng nơ-ron; mô hình và ngưỡng chọn trên validation; test chỉ đánh giá mô hình đã chọn. Môi trường: Python 3.15.2, torch 2.15.0, macOS host. Chạy lại notebook 08 cho kết quả giống hệt (seed cố định).

| Notebook | Train → test | Biến | Mô hình chọn | ROC-AUC test (bootstrap 95%) | PR-AUC | Precision | Recall | F1 | Ngưỡng | Chi tiết |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 02 BRFSS (cũ, để so sánh) | 2021–22 → 2023 | 5 | hist_gradient_boosting | 0,7648 (0,7630–0,7663) | 0,330 | 0,297 | 0,600 | 0,398 | — | [report](../../artifacts/notebook_runs/brfss/20261105T082221_854019Z/report.json) |
| [07 BRFSS 20 biến](07_BRFSS_20_Bien.ipynb) | 2021–22 → 2023 | 20 | neural_seed_42 (MLP) | **0,8217** (0,8198–0,8232) | 0,425 | 0,365 | 0,632 | 0,463 | 0,65 | [report](../../artifacts/notebook_runs/brfss20/20261112T073448_850428Z/report.json) |
| [08 BRFSS 22 biến](08_BRFSS_22_Bien_Huyet_Ap.ipynb) | 2021 → 2023 | 22 (+ tăng huyết áp, cholesterol) | neural_seed_43 (MLP) | **0,8349** (0,8332–0,8363) | 0,450 | 0,380 | 0,652 | 0,480 | 0,65 | [report](../../artifacts/notebook_runs/brfss22/20261112T075023_620271Z/report.json) |
| 04 NHANES 15 (cũ, để so sánh) | 2015–16 → 2017–18 | 15 | neural_seed_42 (CNN) | 0,9314 (0,9130–0,9487) | 0,795 | 0,758 | 0,752 | 0,755 | 0,8 | [report](../../artifacts/notebook_runs/nhanes15/20261105T081930_945286Z/report.json) |
| [09 NHANES 5 chu kỳ](09_NHANES15_Nhieu_Chu_Ky.ipynb) | 2011–16 → 2017–18 | 15 | hist_gradient_boosting | **0,9468** (0,9335–0,9583) | 0,822 | 0,783 | 0,778 | 0,781 | 0,7 | [report](../../artifacts/notebook_runs/nhanes15_multi/20261112T073408_304203Z/report.json) |
| 09 — test ngoài | cùng mô hình → 2021–23 (n=2.843, 382 dương) | 15 | hist_gradient_boosting | 0,9527 | 0,833 | 0,764 | 0,770 | 0,767 | 0,7 | như trên |

Cỡ mẫu: BRFSS 07 train 683.070 / validation 170.768 / test 418.492 (14,3% dương); BRFSS 08 train 339.166 / validation 84.792 / cùng test; NHANES 09 train 5.265 / validation 1.343 / test 2.038 (bản cũ train 1.680).

**Biến quan trọng nhất (permutation importance, validation, ROC-AUC giảm khi xáo trộn):**
- BRFSS 07: nhóm tuổi 0,074 · sức khỏe tự đánh giá 0,043 · BMI 0,037 · lần khám gần nhất 0,022 · bệnh thận 0,005 · bệnh mạch vành 0,004.
- BRFSS 08: nhóm tuổi 0,036 · sức khỏe tự đánh giá 0,033 · BMI 0,025 · tăng huyết áp 0,016 · lần khám gần nhất 0,013 · cholesterol cao 0,012.
- NHANES 09: HbA1c 0,130 · glucose lúc đói 0,020 · tuổi 0,011 · cholesterol toàn phần 0,009; các biến còn lại gần 0.

**Diễn giải và giới hạn.** So sánh 02→07 và 04→09 là trên **cùng tập test** nên chênh lệch phản ánh tác động của dữ liệu thêm. 07→08 có tập train khác (chỉ 2021) nên chỉ tham khảo. NHANES bị chi phối bởi HbA1c — chính tiêu chuẩn chẩn đoán — nên điểm cao không đồng nghĩa phát hiện bệnh "ẩn". "Lần khám gần nhất" quan trọng ở BRFSS gợi ý nhãn tự khai phụ thuộc việc có đi khám (người không khám thì không được "thông báo mắc"). Test 2023 và 2017–18 đã được xem trong các lần chạy trước. Không dùng survey weight; dữ liệu Hoa Kỳ; không phải chẩn đoán.

## NAGALA (Nhật Bản) — dự báo mắc mới, notebook 10

Khác 02–09 (tình trạng hiện tại), đây là bài toán **dự báo mắc đái tháo đường mới** (theo dõi trung vị khoảng 5 năm). 15.464 người khám sức khoẻ, 373 ca dương (2,4%); chia stratified 60/20/20 (train 9.278 / validation 3.093 / test 3.093, test có 74 ca dương). Mô hình chọn theo ROC-AUC validation, ngưỡng theo F1 validation, test dùng một lần mỗi phiên bản. Brier là sau hiệu chỉnh Platt fit trên validation (Brier chỉ dùng tỷ lệ nền: 0,0234). Báo cáo: [report](../../artifacts/notebook_runs/nagala/20261112T081722_701428Z/report.json).

| Phiên bản | Mô hình chọn | ROC-AUC test (bootstrap 95%) | PR-AUC (95%) | Precision | Recall | F1 | Ngưỡng | Brier |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A: có glucose đói + HbA1c (18 biến) | neural_seed_42 (MLP) | **0,864** (0,813–0,907) | **0,236** (0,171–0,334) | 0,220 | 0,527 | 0,311 | 0,85 | 0,0205 |
| B: không glucose/HbA1c (16 biến) | logistic_regression | 0,808 (0,763–0,854) | 0,085 (0,067–0,121) | 0,094 | 0,230 | 0,134 | 0,8 | 0,0228 |

PR-AUC của mô hình ngẫu nhiên là 0,024. Quan trọng nhất (permutation importance, validation): A: glucose đói 0,072 · HbA1c 0,066 · tuổi 0,018 · triglyceride 0,010; B: tuổi 0,052 · BMI 0,038 · gan nhiễm mỡ 0,024 · ALT 0,018.

**Diễn giải.** Xét nghiệm đường huyết nâng PR-AUC từ 0,085 lên 0,236 và ROC-AUC từ 0,81 lên 0,86; không có chúng, mô hình chỉ hơn ngẫu nhiên khoảng 3,5 lần về PR-AUC. Tại ngưỡng của A, phát hiện 39/74 ca mắc mới nhưng kèm 138 báo động sai (precision 22%). Điểm thô của mô hình dùng trọng số lớp nên không phải xác suất; chỉ sau hiệu chỉnh Brier mới nhỉnh hơn mức chỉ-tỷ-lệ-nền (0,0205 so với 0,0234; B gần như không cải thiện).

**Giới hạn.** Dân số Nhật Bản, người đi khám sức khoẻ định kỳ ở một bệnh viện, không phải người Việt; chỉ 74 ca dương ở test nên khoảng tin cậy rộng và xếp hạng các mô hình gần nhau không đáng tin. Tiêu chí loại người đã mắc lúc baseline và tiêu chí chẩn đoán mắc mới chưa xác minh từ toàn văn (dữ liệu baseline HbA1c tối đa 6,4%, glucose tối đa 109 mg/dL cho thấy không có người đã mắc). Đã loại `Follow up duration, days` (rò rỉ), mã bệnh nhân, các cột suy ra/trùng đơn vị. Không xử lý thời gian theo dõi khác nhau (không phân tích sống còn); không validation ngoài; không dùng chẩn đoán/sàng lọc.
