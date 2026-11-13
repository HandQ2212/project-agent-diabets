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

## BRFSS 2015–2023 (notebook 11) — bộ dữ liệu lớn

Mở rộng notebook 07 từ 3 năm lên **9 năm BRFSS (2015–2023)**, 3.830.441 dòng sau lọc nhãn. Chia **theo thời gian**: train 2015–2021 (2.982.069), validation 2022 (429.880), test 2023 (418.492, cùng các dòng với notebook 07). Tiền xử lý fit chỉ trên train; MLP 3 seed học trên toàn bộ train (không phải lấy mẫu con); chọn mô hình theo ROC-AUC validation, ngưỡng theo F1 validation. Run [`brfss_2015_2023/20261112T132422_619456Z`](../../artifacts/notebook_runs/brfss_2015_2023/20261112T132422_619456Z/report.json). Thời gian chạy toàn notebook khoảng 10 phút 28 giây trên CPU (train: LR 3 giây, HGB 32 giây, MLP 124–146 giây mỗi seed).

| | 07 (2021–22 → 2023) | 11 (2015–21 → 2023) |
| --- | --- | --- |
| Train / validation / test | 683.070 / 170.768 / 418.492 | 2.982.069 / 429.880 / 418.492 |
| Cách chia validation | ngẫu nhiên 20% của 2021–22 (cùng năm với train) | cả năm 2022 (năm sau train) |
| Mô hình chọn, ngưỡng | MLP seed 42, 0,65 | MLP seed 42, 0,65 |
| ROC-AUC test (bootstrap 95%) | 0,8217 (0,8198–0,8232) | **0,8214** (0,8195–0,8228) |
| PR-AUC | 0,425 | 0,425 |
| Precision / Recall / F1 | 0,365 / 0,632 / 0,463 | 0,369 / 0,619 / 0,462 |

**Kết luận trung thực: thêm 6 năm dữ liệu cũ (gấp 4,4 lần dữ liệu train) không cải thiện mô hình.** ROC-AUC test chênh −0,0003, khoảng tin cậy chồng lên nhau gần như hoàn toàn. Hai kiểm tra bổ sung ủng hộ điều này. (a) Cùng HistGradientBoosting, cùng test 2023, chỉ đổi cửa sổ năm train: 2021 (424 nghìn dòng) 0,8202 · 2020–21 0,8203 · 2018–21 0,8204 · 2015–21 (2,98 triệu dòng) 0,8202. Trên validation 2022: 0,8229 · 0,8231 · 0,8234 · 0,8233. Đường học đã **phẳng từ khoảng 400 nghìn dòng**; 20 biến này không chứa thêm thông tin mà dữ liệu nhiều hơn khai thác được. (b) ROC-AUC của mô hình đã chọn theo năm: 0,830–0,833 ở các năm train (trong mẫu), 0,8245 ở validation 2022, 0,8214 ở test 2023, tức giảm nhẹ khi đi xa khỏi giai đoạn train. Độ chênh nhỏ và chưa tách được dịch chuyển phân phối khỏi nhiễu. Tỷ lệ dương gần ổn định (13,3–14,3% mỗi năm).

Lợi ích thực tế của bộ lớn là độ chắc của ước lượng (khoảng bootstrap và validation ổn định hơn, ba seed gần như trùng: val AUC 0,8245/0,8245/0,8244), không phải điểm số cao hơn. Muốn tăng chất lượng phải thêm thông tin (biến mới, ví dụ huyết áp/cholesterol như notebook 08) chứ không phải thêm năm. HGB đạt 0,8233 trên validation, sát MLP (0,8245). LR 0,8188.

Biến quan trọng nhất (permutation importance, validation): nhóm tuổi 0,079 · sức khỏe tự đánh giá 0,053 · BMI 0,036 · lần khám gần nhất 0,018 · mạch vành 0,005 · bệnh thận 0,004.

**Hài hoà biến (chi tiết trong notebook và `docs/DATA.md`).** 20 biến của notebook 07 được giữ, nhưng cột nguồn đổi theo năm (đối chiếu codebook CDC và nhãn biến trong file XPT): giới `SEX` (2015–17) / `SEX1` (2018) / `SEXVAR` (2019+); thận `CHCKIDNY` / `CHCKDNY1` (2018) / `CHCKDNY2`; COPD `CHCCOPD1` / `CHCCOPD2` / `CHCCOPD3`; trầm cảm `ADDEPEV2` → `ADDEPEV3`; rượu nhiều `_RFDRHV5/6/7/8`; bảo hiểm `HLTHPLN1` → `_HLTHPLN` → `_HLTHPL1`; chi phí khám `MEDCOST` → `MEDCOST1`; nhãn `DIABETE3` (2015–18) → `DIABETE4` (2019+). `_PHYS14D`/`_MENT14D` không có trong file 2015 nên suy ra từ `PHYSHLTH`/`MENTHLTH` (công thức khớp 100% biến chính thức của CDC ở cả 8 năm còn lại). Thu nhập `_INCOMG` (5 mức, 2015–20) và `_INCOMG1` (7 mức, 2021+) gộp về 5 mức. **Bị bỏ:** tăng huyết áp (`_RFHYPE5/6`) và cholesterol cao (`_RFCHOL1/2/3`) vì chỉ có ở năm lẻ. Nhãn giống 07: `DIABETE3/4` = 1 thành 1, = 3 thành 0; loại 2 (chỉ khi mang thai), 4 (tiền đái tháo đường), 7/9 và trống.

**Giới hạn.** Một số biến đổi định nghĩa giữa các năm mà không thể hài hoà hoàn toàn: bảo hiểm 2023 (`_HLTHPL1`) dựa trên câu hỏi loại bảo hiểm chính (PRIMINS1) nên tỷ lệ "không có" khác; câu `MEDCOST` đổi chữ từ 2021; BRFSS có thay đổi phương pháp và dịch chuyển COVID ở 2020. Thu nhập gộp 5 mức mất chi tiết so với 07 (7 mức) nên hai notebook không hoàn toàn cùng đặc trưng. Validation khác nhau (2022 so với ngẫu nhiên 20% của 2021–22) nên việc chọn ngưỡng và seed không tương đương; chỉ test là cùng một. Mô hình 11 không được train trên 2022 (07 có), nên so sánh chưa thật sự công bằng về năm gần nhất. Test 2023 đã được xem nhiều lần. Phân tích cửa sổ train dùng test nhưng chỉ để chẩn đoán, không chọn mô hình. Không dùng survey weight; dữ liệu Hoa Kỳ; nhãn tự khai; nhân quả ngược với bệnh kèm; không dùng chẩn đoán/sàng lọc.

## NAGALA (Nhật Bản) — dự báo mắc mới, notebook 10

Khác 02–09 (tình trạng hiện tại), đây là bài toán **dự báo mắc đái tháo đường mới** (theo dõi trung vị khoảng 5 năm). 15.464 người khám sức khoẻ, 373 ca dương (2,4%); chia stratified 60/20/20 (train 9.278 / validation 3.093 / test 3.093, test có 74 ca dương). Mô hình chọn theo ROC-AUC validation, ngưỡng theo F1 validation, test dùng một lần mỗi phiên bản. Brier là sau hiệu chỉnh Platt fit trên validation (Brier chỉ dùng tỷ lệ nền: 0,0234). Báo cáo: [report](../../artifacts/notebook_runs/nagala/20261112T081722_701428Z/report.json).

| Phiên bản | Mô hình chọn | ROC-AUC test (bootstrap 95%) | PR-AUC (95%) | Precision | Recall | F1 | Ngưỡng | Brier |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A: có glucose đói + HbA1c (18 biến) | neural_seed_42 (MLP) | **0,864** (0,813–0,907) | **0,236** (0,171–0,334) | 0,220 | 0,527 | 0,311 | 0,85 | 0,0205 |
| B: không glucose/HbA1c (16 biến) | logistic_regression | 0,808 (0,763–0,854) | 0,085 (0,067–0,121) | 0,094 | 0,230 | 0,134 | 0,8 | 0,0228 |

PR-AUC của mô hình ngẫu nhiên là 0,024. Quan trọng nhất (permutation importance, validation): A: glucose đói 0,072 · HbA1c 0,066 · tuổi 0,018 · triglyceride 0,010; B: tuổi 0,052 · BMI 0,038 · gan nhiễm mỡ 0,024 · ALT 0,018.

**Diễn giải.** Xét nghiệm đường huyết nâng PR-AUC từ 0,085 lên 0,236 và ROC-AUC từ 0,81 lên 0,86; không có chúng, mô hình chỉ hơn ngẫu nhiên khoảng 3,5 lần về PR-AUC. Tại ngưỡng của A, phát hiện 39/74 ca mắc mới nhưng kèm 138 báo động sai (precision 22%). Điểm thô của mô hình dùng trọng số lớp nên không phải xác suất; chỉ sau hiệu chỉnh Brier mới nhỉnh hơn mức chỉ-tỷ-lệ-nền (0,0205 so với 0,0234; B gần như không cải thiện).

**Giới hạn.** Dân số Nhật Bản, người đi khám sức khoẻ định kỳ ở một bệnh viện, không phải người Việt; chỉ 74 ca dương ở test nên khoảng tin cậy rộng và xếp hạng các mô hình gần nhau không đáng tin. Tiêu chí loại người đã mắc lúc baseline và tiêu chí chẩn đoán mắc mới chưa xác minh từ toàn văn (dữ liệu baseline HbA1c tối đa 6,4%, glucose tối đa 109 mg/dL cho thấy không có người đã mắc). Đã loại `Follow up duration, days` (rò rỉ), mã bệnh nhân, các cột suy ra/trùng đơn vị. Không xử lý thời gian theo dõi khác nhau (không phân tích sống còn); không validation ngoài; không dùng chẩn đoán/sàng lọc.
