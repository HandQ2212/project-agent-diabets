# Khảo sát bộ dữ liệu có thể lấy được thật — đồ án "Đường An"

Ngày rà soát: 12/11/2026. Tiếp nối `DATASET_CANDIDATES_VIETNAM.md` (05/11) và `DATA.md`. Lần này **đã kiểm tra trực tiếp trang gốc** và, với hai bộ Dryad, **đã tải thử vào thư mục tạm ngoài dự án** để đọc tên cột/nhãn (không đưa vào `data/`).

Cách ghi độ tin cậy: **[ĐÃ XÁC MINH]** = tôi đọc trực tiếp trang gốc hoặc chính file; **[CHƯA XÁC MINH]** = suy ra từ nguồn thứ cấp hoặc không truy cập được trang gốc. Mọi khẳng định đều kèm URL.

## 1. Bảng tổng hợp

| Bộ dữ liệu | Dân số | Truy cập | Giấy phép / điều khoản | Số dòng | Nhãn đái tháo đường | Dùng ngay được? | Công sức |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **WHO STEPS Việt Nam 2021** | Người Việt 18–69 tuổi, toàn quốc | Đăng ký tài khoản + "Get Microdata" (chi tiết bước yêu cầu **chưa xác minh**) | Public-use; phi thương mại, ghi nguồn, gửi kế hoạch công bố cho WHO, mời điều phối viên khảo sát đồng tác giả | 4.435 (186 biến) | Không có cột nhãn sẵn: tự dựng từ `b5` (glucose đói) + `h7a/h8/h9` (tự khai, thuốc, insulin). Cắt ngang | **Chưa** (cần tài khoản do bạn tự tạo) | Trung bình |
| **Rich Healthcare (Trung Quốc)** | 211.833 người lớn ≥20 tuổi, 32 điểm khám ở 11 thành phố | **Tải thẳng không đăng nhập** qua bản sao Zenodo (đã kiểm tra) | CC0 | 211.833 × 25 cột | Mắc mới (`censor of diabetes at followup`=1: 4.174 ca, 1,97%) | **Có** | Thấp |
| **NAGALA (Nhật Bản)** | 15.464 người khám sức khỏe (Murakami Memorial Hospital), 8.430 nam / 7.034 nữ | **Tải thẳng không đăng nhập** qua bản sao Zenodo | CC0 | 15.464 × 31 cột | Mắc mới (`Incident DM 0/1`: 373 ca, 2,41%) | **Có** | Thấp |
| Ninh Bình (PMC10297119) | Người Việt nguy cơ cao, thử nghiệm can thiệp lối sống | Xin tác giả ("upon request") | Chưa rõ | 2.153 ban đầu; 500 sau lọc (449/51) | Cột `Outcome` nhưng bài **không nêu tiêu chí** | Chưa | Cao, không chắc kết quả |
| Cohort Việt Nam 5 năm (dme.14680) | Người Việt trung niên | Xin tác giả | Chưa rõ | Chưa rõ | Mắc mới 5 năm | Chưa | Cao, không chắc |
| CHARLS (Trung Quốc ≥45 tuổi) | Người lớn tuổi Trung Quốc | Đăng ký tài khoản, duyệt "trong 3 ngày làm việc" | Đồng ý thỏa thuận đăng ký | Chưa kiểm tra | Chưa kiểm tra | Chưa | Trung bình |
| IFLS (Indonesia) | Hộ gia đình Indonesia | Đăng ký trên RAND, tải miễn phí | Không phân phối lại; gửi bài dùng dữ liệu cho RAND | Chưa kiểm tra | Có HbA1c ở đợt 5 (giọt máu khô, thiên lệch) | Chưa | Trung bình |
| CHNS (Trung Quốc) | Hộ gia đình Trung Quốc | Tải từ Dataverse; dữ liệu cộng đồng cần DUA | Hợp đồng sử dụng dữ liệu cho phần cộng đồng | Chưa kiểm tra | Chưa kiểm tra | Chưa | Trung bình |
| KNHANES (Hàn Quốc) | Người Hàn Quốc | Tải trên website KDCA | Chưa xác minh | Chưa kiểm tra | Chưa kiểm tra | Chưa | Trung bình, rào cản ngôn ngữ |
| Mendeley "T2D Thái Lan" | Chỉ bệnh nhân T2D | Tải mở | CC BY 4.0 | Chưa rõ | Không có nhóm chứng | **Không** | — |

## 2. Chi tiết từng bộ

### 2.1 WHO STEPS Việt Nam 2021 (ưu tiên số 1 về dân số)

**Thông tin xác minh được** [ĐÃ XÁC MINH] từ [trang catalog 948](https://extranet.who.int/ncdsmicrodata/index.php/catalog/948):
- Mã tham chiếu `VNM_2021_STEPS_v01`, do Bộ Y tế Việt Nam thực hiện, thu thập 01–03/2021, phỏng vấn trực tiếp, mẫu cụm nhiều tầng, mỗi hộ chọn một người. Loại "Public-use dataset". Metadata tạo 02/07/2024.
- Ba trọng số: `wStep1` (phỏng vấn), `wStep2` (đo thể chất), `wStep3` (xét nghiệm sinh hóa).
- Điều kiện sử dụng (nguyên văn tóm lược của trang): ghi nhận nguồn dữ liệu; **chia sẻ ấn phẩm dự kiến với WHO trước khi công bố**; **mời đồng tác giả cho điều phối viên khảo sát**; **chỉ dùng phi thương mại, phi lợi nhuận vì sức khỏe cộng đồng**; dữ liệu không bảo hành.
- Câu trích dẫn bắt buộc: "This paper uses data from the [country] [year] STEPS survey … implemented by [implementing agency] with the support of the World Health Organization."
- Liên hệ: NCD Surveillance Team, ncdmonitoring@who.int.
- Tài liệu tải được **không cần đăng nhập** ([related materials](https://extranet.who.int/ncdsmicrodata/index.php/catalog/948/related_materials)): [bảng hỏi](https://extranet.who.int/ncdsmicrodata/index.php/catalog/948/download/6778), [báo cáo quốc gia 3,85 MB](https://extranet.who.int/ncdsmicrodata/index.php/catalog/948/download/6937), [bộ công cụ STEPS v3.2](https://extranet.who.int/ncdsmicrodata/index.php/catalog/948/download/6779).

**Biến liên quan đến đái tháo đường** [ĐÃ XÁC MINH] ([từ điển dữ liệu](https://extranet.who.int/ncdsmicrodata/index.php/catalog/948/data-dictionary/F1), tổng 4.435 bản ghi, 186 biến; trang không hiển thị số hợp lệ từng biến):

| Nhóm | Biến |
| --- | --- |
| Nhân khẩu | `sex`, `age`, `agerange` |
| Tiền sử/thuốc (tự khai) | `h6` đã đo glucose, `h7a` từng được báo cao đường huyết, `h7b` trong 12 tháng qua, `h8` đang dùng thuốc, `h9` đang dùng insulin, `h10`/`h11` thầy lang/thuốc cổ truyền |
| Xét nghiệm | `b1` nhịn ăn, `b5` glucose đói (mmol/l), `b6` đã tiêm insulin hôm nay, `b8` cholesterol toàn phần, `b17` HDL |
| Huyết áp | `m4a/b`, `m5a/b`, `m6a/b` (3 lần đo), `h2a/h3` tăng huyết áp tự khai và thuốc |
| Nhân trắc | `m11` chiều cao, `m12` cân nặng, `m14` vòng eo, `m15` vòng hông (BMI tự tính) |

**Không có** trong từ điển: HbA1c, tiền sử gia đình, triglyceride (không thấy trong phần đã đọc), BMI sẵn. Nghĩa là bộ 15 chỉ số của NHANES hiện tại **không khớp đủ**; phải huấn luyện bộ biến riêng (tuổi, giới, BMI, vòng eo/hông, huyết áp, cholesterol, HDL, [glucose nếu bài toán cho phép]).

**Nhãn và rò rỉ.** Nhãn tự dựng theo định nghĩa STEPS: glucose đói ≥7,0 mmol/l **hoặc** đang dùng thuốc/insulin (cần đối chiếu codebook và báo cáo quốc gia). Nếu nhãn dùng `b5` thì **không được đưa `b5` vào đầu vào** (rò rỉ). Bài toán là *phát hiện cắt ngang*, không phải dự báo mắc mới. Nên có phương án nhãn thay thế: chỉ "đã được chẩn đoán/dùng thuốc" (`h7a/h8/h9`), cho phép giữ `b5` làm đặc trưng nhưng khi đó nhãn là tình trạng đã biết.

**Quy trình yêu cầu microdata.** [CHƯA XÁC MINH phần cuối.] Đã xác nhận:
- Nút "Get Microdata" nằm ở [trang catalog 948](https://extranet.who.int/ncdsmicrodata/index.php/catalog/948) và dẫn tới [trang get-microdata](https://extranet.who.int/ncdsmicrodata/index.php/catalog/948/get-microdata). Khi tôi tải trang này không đăng nhập, nội dung **trả về rỗng**; phần tử nút mang lớp `icon-da-licensed` (kiểu "licensed" của phần mềm NADA).
- Trang [đăng nhập](https://extranet.who.int/ncdsmicrodata/index.php/auth/login) có nút **Register** (email + mật khẩu + captcha). Hệ thống chuyển 401 về trang đăng nhập.
- Tài liệu thứ cấp ([vignette gói R stepssurvey](https://cran.ms.unimelb.edu.au/web/packages/stepssurvey/vignettes/validation.html)) nói dữ liệu STEPS lấy "under license", "subject to the WHO STEPS data access agreement", **không được phân phối lại**. WHO nói chung: "datasets for most surveys are publicly available" ([trang WHO](https://www.who.int/teams/noncommunicable-diseases/surveillance/data)).
- Chưa tìm được văn bản nào nêu rõ biểu mẫu yêu cầu hỏi gì, thời gian duyệt, hay có cấp tức thì sau khi đồng ý điều khoản hay không. Cách duy nhất để biết là bạn đăng ký và bấm nút (xem mục 4).

**Lưu ý hạn chế.** Sử dụng cho đồ án/demo website: điều khoản là "phi thương mại vì sức khỏe cộng đồng"; đồ án học thuật thường phù hợp nhưng nên ghi câu hỏi này trong email gửi WHO. Ngoài ra không đăng lại microdata trong repo công khai (không phân phối lại).

**STEPS 2015** ([catalog 590](https://extranet.who.int/ncdsmicrodata/index.php/catalog/590)) [ĐÃ XÁC MINH]: public-use, điều kiện giống 2021; thu thập 08/2015; 3.856 người tham gia, 3.758 hoàn thành Bước 1, 3.080 hoàn thành cả 3 bước. Là mẫu độc lập khác người so với 2021 (khảo sát cắt ngang khác năm; việc có trùng người hay không **chưa xác minh**), dùng để kiểm định ngoài sau khi đã có 2021.

### 2.2 Rich Healthcare, Trung Quốc (Dryad / Zenodo)

Nguồn: [Dryad doi:10.5061/dryad.ft8750v](https://datadryad.org/dataset/doi:10.5061/dryad.ft8750v); bài gốc: Chen et al., BMJ Open 2018 ([bản tóm tắt](https://bmjopen.bmj.com/content/8/9/e021768.abstract)).

**Giấy phép và truy cập.** [ĐÃ XÁC MINH]
- Giấy phép **CC0 1.0** theo API Dryad (`license: https://spdx.org/licenses/CC0-1.0.html`) và theo [bản sao Zenodo](https://zenodo.org/records/4997196). Trang web Dryad chỉ ghi chung "licensed for reuse".
- API/đường dẫn tệp của Dryad **không dùng được khi không đăng nhập** (API trả 401, `file_stream` trả 403 với `curl`). Có thể tải qua nút "Download" trên trình duyệt, tôi không kiểm chứng được.
- **Đường dẫn trực tiếp không cần đăng nhập** (HTTP 200, 28.340.131 byte; MD5 tệp tôi tải về = `b468cc3704b11ba1bd21532451fe2856`, **trùng hoàn toàn** MD5 mà Dryad công bố):
  `https://zenodo.org/records/4997196/files/RC%20Health%20Care%20Data-20180820.xlsx?download=1`
- Đây là bản sao Zenodo mang cùng DOI Dryad, một tệp `RC Health Care Data-20180820.xlsx` (xlsx, 28,3 MB). Công bố 21/08/2018.

**Cột thực tế (đã mở tệp, 211.833 dòng × 25 cột; không thiếu ở các cột sau trừ khi ghi):**
`id`, `Age (y)` (20–99), `Gender(1 nam; 2 nữ)`, `site`, `height(cm)`, `weight(kg)`, `BMI(kg/m2)`, `SBP`, `DBP` (thiếu ~24), `FPG (mmol/L)` (0,59–6,99), `Cholesterol` (thiếu 4.854), `Triglyceride` (thiếu 4.887), `HDL-c` (**thiếu 94.562**), `LDL` (thiếu 93.421), `ALT` (thiếu 1.782), `AST` (**thiếu 123.290**), `BUN` (thiếu 21.551), `CCR` (thiếu 11.175), `FPG of final visit(mmol/L)`, `Diabetes diagnosed during followup（1,Yes）`, `censor of diabetes at followup(1, Yes; 0, No)`, `year of followup` (2,0–7,6), `smoking status` (**thiếu 151.603**), `drinking status` (thiếu 151.603), `family histroy of diabetes(1,Yes;0,No)` (có đủ; 4.344 người có).
- **Không có**: vòng eo, HbA1c.

**Nhãn.** Bài gốc: đái tháo đường = glucose đói ≥7,00 mmol/l **và/hoặc** tự khai; kiểm duyệt tại thời điểm chẩn đoán hoặc lần khám cuối; theo dõi trung vị 3,1 năm; glucose đo bằng glucose oxidase, Beckman 5800 ([PMC6169758 qua truy vấn tìm kiếm](https://pmc.ncbi.nlm.nih.gov/articles/PMC6169758); tôi không đọc được toàn văn do chặn trình duyệt). Trong tệp: cột `censor of diabetes at followup`=1 có **4.174** dòng, khớp con số 4.174 ca của bài báo. Cột `Diabetes diagnosed during followup` chỉ có **1.304** giá trị 1 (còn lại trống) nên **không phải nhãn đầy đủ**; dùng cột `censor...`. Chưa rõ vì sao hai cột khác nhau; ghi lại trong notebook.

**Rò rỉ cần tránh.** `FPG of final visit` (đo sau thời điểm gốc) và `year of followup` (hậu kết cục) **không được** đưa vào đặc trưng khi dự báo. `FPG` gốc tối đa 6,99 nên mọi người đều chưa mắc ở thời điểm gốc (kiểm tra bằng dữ liệu). Cohort **dọc**, có thời gian theo dõi → dùng được cho dự báo mắc mới và mô hình sống còn.

### 2.3 NAGALA, Nhật Bản (Dryad / Zenodo)

Nguồn: [Dryad doi:10.5061/dryad.8q0p192](https://datadryad.org/dataset/doi:10.5061/dryad.8q0p192); bài gốc Okamura T. et al., *Int J Obes* 2019;43:139–148, DOI 10.1038/s41366-018-0076-3 (xem [mô tả từ MEDLINE](https://pesquisa.bvsalud.org/bvsdip/resource/pt/mdl-29717276)).

**Truy cập và giấy phép.** [ĐÃ XÁC MINH] CC0 theo API Dryad và [bản sao Zenodo 4996032](https://zenodo.org/records/4996032). Tệp `Data set Int J Obesity.xlsx`, 3.255.571 byte, MD5 = `47edfb147078657a0eecfff7f9364532` (trùng MD5 Dryad). Đường dẫn trực tiếp không đăng nhập:
`https://zenodo.org/records/4996032/files/Data%20set%20Int%20J%20Obesity.xlsx?download=1`
Công bố 19/02/2019. Như Rich Healthcare, API/`file_stream` của Dryad không dùng được khi chưa đăng nhập.

**Cột thực tế (đã mở tệp: 15.464 dòng × 31 cột, gần như không thiếu):** `Sex`, `Baseline Age` (18–79), `Ethanol g/wk`, `Fatty liver 0/1`, `BMI`, `Waist circumference (cm)`, `WC≥90/80`, `BMI≥25`, `Obesity phenotype 1-8`, `Follow up duration, days` (164–4.732), `ALT`, `AST`, `Body Weight`, `Habit of exercise`, `GGT`, `HDL` (mg/dL và mmol/L), `Total Cholesterol` (hai đơn vị), `Triglycerides` (hai đơn vị), `HbA1c` (% và mmol/mol), `Alcohol` (1–4), `Smoking` (1–3), `Fasting plasma glucose` (mg/dL, mmol/L), `Systolic BP`, `Diastolic BP`, `Incident DM 0/1`.
- **Điểm lưu ý**: cột giới tính ghi "1:Men, 2:Women" nhưng giá trị thực là 1 (8.430) và 0 (7.034), tức 0 = nữ. `HDL mmol/L` có giá trị 0 ở 11 dòng mà bản mg/dL thiếu — dùng bản mg/dL, coi 0 là thiếu. Các cặp cột trùng đơn vị cần bỏ một cột. `Obesity phenotype` và `WC≥…`, `BMI≥25` là biến suy ra, không dùng kèm biến gốc nếu muốn tránh đa cộng tuyến.
- **Không có**: tiền sử gia đình.

**Nhãn.** `Incident DM 0/1`: 373 ca / 15.464 (2,41%); theo bài gốc, 286 nam và 87 nữ mắc mới (khớp 373). Tiêu chí chẩn đoán chính xác **chưa xác minh từ bài gốc** (không đọc được toàn văn); một nghiên cứu thứ cấp dùng cùng dữ liệu định nghĩa là HbA1c ≥6,5%, glucose đói ≥7 mmol/l hoặc tự khai (đã nêu trong kết quả tìm kiếm, **thứ cấp**). Baseline `HbA1c` tối đa 6,4% và `FPG` tối đa 109 mg/dL nên mọi người chưa mắc ở thời điểm gốc. Theo dõi trung vị 5,8 năm (nam) / 5,1 năm (nữ). Cohort dọc.

**Bộ biến đồng cấu với dự án.** NAGALA là bộ **gần bộ biến của "Đường An" nhất** trong ba bộ Đông Á: tuổi, giới, BMI, vòng eo, huyết áp, glucose, HbA1c, cholesterol, HDL, TG.

### 2.4 Nghiên cứu Ninh Bình

Nguồn [PMC10297119](https://pmc.ncbi.nlm.nih.gov/articles/PMC10297119/) (đọc qua [Europe PMC](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10297119/fullTextXML)) [ĐÃ XÁC MINH một phần, chỉ đọc 100.000 ký tự đầu]:
- 2.153 người ≥18 tuổi từ thử nghiệm can thiệp lối sống ở Ninh Bình; IRB Đại học Y Hà Nội, mã DS10-A1.
- 13 thuộc tính: tuổi, giới, BMI, insulin, huyết áp tâm trương/tâm thu, glucose đói, glucose sau 2 giờ, cholesterol toàn phần, triglyceride, HDL, vòng eo, vòng hông. Cột `Outcome` nhị phân.
- Bài **không nêu tiêu chí gán nhãn**; nếu nhãn dựa trên glucose đói/OGTT thì rất dễ rò rỉ.
- Sau khi lọc thiếu và ngoại lai còn 500 mẫu (449 không / 51 có bệnh); bài còn có số liệu train/test không khớp (628/270). Cộng thêm tập ngoài 67 người.
- Data availability: "available from the corresponding author upon request".
- Kết luận: rất tốt về dân số nhưng chỉ 500 mẫu, mất cân bằng, nhóm nguy cơ cao, không có điều khoản; **chỉ nên theo như đường song song** (một email).

### 2.5 Các bộ Đông và Đông Nam Á khác

| Bộ | Kết quả kiểm tra | Nhận xét |
| --- | --- | --- |
| **CHARLS** | Trang [charls.pku.edu.cn](https://charls.pku.edu.cn/en/) có "Sign in/Sign up". [FAQ chính thức](https://charls.pku.edu.cn/en/Faq/Frequently_Asked_Questions.htm): đăng ký bằng thỏa thuận, cung cấp thông tin thật, xác nhận email, đơn xin tập dữ liệu công khai "reviewed and approved in 3 working days" [ĐÃ XÁC MINH]. Các đợt: nền 2011, 2013, đợt 4 (2018) phát hành 23/09/2020, đợt 5 (2020) phát hành 16/11/2023. Đợt có HbA1c/glucose [CHƯA XÁC MINH]: nguồn thứ cấp nói máu toàn phần được lưu để đo HbA1c ([hồ sơ cohort 2014](https://pmc.ncbi.nlm.nih.gov/articles/PMC3937970)). Trang cảnh báo "under review for potential modification". | Dân số ≥45 tuổi, ít liên quan người Việt trẻ; chỉ là phương án thứ ba. |
| **IFLS (Indonesia)** | [Trang tải RAND](https://www.rand.org/health/surveys/FLS/IFLS/download.html) trả 403 với tôi. Nguồn thứ cấp ([danh sách biomarker](https://biomarker-network.isr.umich.edu/studies-with-biomarkers/ifls/) và kết quả tìm kiếm): đăng ký, miễn phí, không phân phối lại, gửi bài dùng dữ liệu cho RAND, HbA1c có ở đợt 5 từ giọt máu khô, **đo giọt máu khô thiên lệch lên khi HbA1c <8%** (Thomas 2018). [CHƯA XÁC MINH trực tiếp] | Đông Nam Á nhưng HbA1c chất lượng thấp, dùng phải hiệu chỉnh. |
| **CHNS** | [Trang datasets](https://chns.cpc.unc.edu/data/datasets): dữ liệu hộ/cá nhân tải ở Dataverse định dạng SAS; dữ liệu cộng đồng cần DUA do giám đốc dự án duyệt; hỏi chns@unc.edu. Không thấy mô tả biến glucose/HbA1c trên trang này. [ĐÃ XÁC MINH một phần] | Đợt đo sinh học 2009 chưa xác minh. Dữ liệu cũ (đến 2015). |
| **KNHANES** | Trang tiếng Anh [knhanes.kdca.go.kr/knhanes/eng](https://knhanes.kdca.go.kr/knhanes/eng/main.do) chỉ có điều hướng; không đọc được quy trình tải. Nguồn thứ cấp: tải SAS/SPSS miễn phí, phát hành tháng 12 năm sau khảo sát ([bài tổng quan](https://pmc.ncbi.nlm.nih.gov/articles/PMC4017741)); dữ liệu liên kết tử vong là sản phẩm riêng qua KDCA/MDIS. [CHƯA XÁC MINH] Chưa tìm được quy tắc cho người nước ngoài. | Cùng loại cắt ngang với NHANES, trùng vai trò; ưu tiên thấp. |
| **Ấn Độ, Thái Lan (khảo sát quốc gia)** | Không kiểm tra được trong lượt này. | Bỏ qua. |
| **Mendeley "T2D Thái Lan"** ([xhmjcfp2ym](https://data.mendeley.com/datasets/xhmjcfp2ym/1)) | CC BY 4.0, DOI 10.17632/xhmjcfp2ym.1, 21/10/2020, `MontiFinal.csv` + `DataDictionary.xls`; **chỉ bệnh nhân T2D**, mục tiêu tâm lý-xã hội/kiểm soát, không có nhóm chứng. | **Không dùng** để phân loại có/không bệnh. |
| **Kho dữ liệu Việt Nam trên Mendeley/Figshare/Zenodo/PhysioNet** | Tìm kiếm không thấy bộ dữ liệu cá nhân người Việt về đái tháo đường được công khai; kết quả chỉ là bài báo, một mẫu vi sinh vật ruột 7+7 người, thử nghiệm giáo dục (ClinicalTrials.gov ghi **không chia sẻ dữ liệu cá nhân**: [NCT04403841](https://clinicaltrials.gov/study/NCT04403841)). | Chưa có nguồn mở cho người Việt ngoài STEPS. |

**Cờ cảnh báo chung.** Bộ dữ liệu trên Kaggle/Hugging Face không rõ nguồn hoặc tổng hợp không được dùng làm nhãn thật. Ví dụ kết quả tìm kiếm có bản [Synthetic-Diabetes-Dataset](https://huggingface.co/datasets/MaxPrestige/Synthetic-Diabetes-Dataset) tự gọi là tổng hợp. Giữ nguyên quyết định đã loại Pima và CDC Diabetes Health Indicators.

## 3. So sánh để chọn

| Tiêu chí | STEPS VN 2021 | NAGALA | Rich Healthcare |
| --- | --- | --- | --- |
| Gần người Việt | Cao nhất | Thấp (Nhật) | Thấp (Trung Quốc) |
| Lấy được ngay hôm nay | Cần đăng ký | **Có** | **Có** |
| Bài toán | Phát hiện cắt ngang | Dự báo mắc mới | Dự báo mắc mới |
| Biến khớp "Đường An" | Tuổi, giới, BMI (tự tính), vòng eo, huyết áp, cholesterol, HDL; không HbA1c/TG/tiền sử | **Tuổi, giới, BMI, vòng eo, huyết áp, glucose, HbA1c, cholesterol, HDL, TG** | Tuổi, giới, BMI, huyết áp, glucose, lipid, tiền sử gia đình; không vòng eo/HbA1c |
| Cỡ mẫu / số ca dương | 4.435 / chưa biết | 15.464 / 373 | 211.833 / 4.174 |
| Nguy cơ pháp lý | Điều khoản WHO | CC0 | CC0 |
| Nguy cơ rò rỉ | Cao nếu nhãn dùng `b5` | Thấp (biến gốc đều trước kết cục) | Phải bỏ `FPG of final visit` |

## 4. Khuyến nghị: hai việc nên làm tiếp

### Ưu tiên 1: WHO STEPS Việt Nam 2021 (bạn phải tự làm, tôi không đăng ký/đồng ý điều khoản thay)

Đây là bộ duy nhất của người Việt có thể lấy được nên nó đáng làm dù mất công. Các bước:
1. Mở https://extranet.who.int/ncdsmicrodata/index.php/auth/login và bấm **Register**. Dùng email trường/cá nhân thật, nhập đúng thông tin (form đăng ký hỏi email, mật khẩu, captcha).
2. Đăng nhập, vào https://extranet.who.int/ncdsmicrodata/index.php/catalog/948 và bấm **Get Microdata**. Nếu hiện biểu mẫu yêu cầu, điền: mục đích (đồ án môn học, mô hình sàng lọc phi thương mại), cơ quan (trường đại học), và nêu rõ cách bạn sẽ ghi nguồn. **Đọc kỹ rồi tự chấp nhận điều khoản.**
3. Chụp màn hình trang yêu cầu và email xác nhận làm bằng chứng. Nếu 1 tuần chưa có phản hồi, viết email tới ncdmonitoring@who.int nêu mã `VNM_2021_STEPS_v01`, mục đích, và hỏi (a) có dùng được cho đồ án + demo website không, (b) quy trình duyệt, (c) nghĩa vụ "offer co-authorship" áp dụng thế nào với báo cáo môn học.
4. Tải cả hai định dạng nếu có (CSV/Stata/SPSS) vào `data/raw/steps_vn2021/` (kiểm tra `.gitignore` đã loại thư mục này; **không commit microdata**, vì có thể bị cấm phân phối lại). Tải thêm [từ điển](https://extranet.who.int/ncdsmicrodata/index.php/catalog/948/data-dictionary/F1) và [báo cáo quốc gia](https://extranet.who.int/ncdsmicrodata/index.php/catalog/948/download/6937) để đối chiếu định nghĩa đái tháo đường của STEPS.
5. Việc cần làm sau khi có dữ liệu: đếm số ca có `b5` hợp lệ và số ca dương; quyết định nhãn; áp trọng số `wStep3` khi báo cáo.

Dự phòng/song song: gửi email xin dữ liệu tác giả Ninh Bình (địa chỉ có trong bài [PMC10297119](https://pmc.ncbi.nlm.nih.gov/articles/PMC10297119/)); hỏi cụ thể tiêu chí gán `Outcome`, điều kiện sử dụng, mã hóa cột.

### Ưu tiên 2: NAGALA (rồi Rich Healthcare làm bản kiểm tra lớn) — không cần đăng ký

Bạn có thể tải ngay, không điều khoản ràng buộc ngoài trích dẫn tử tế (CC0 không yêu cầu, nhưng nên trích bài gốc):
1. Tải `https://zenodo.org/records/4996032/files/Data%20set%20Int%20J%20Obesity.xlsx?download=1` (3,26 MB) vào `data/raw/nagala/`; kiểm tra MD5 `47edfb147078657a0eecfff7f9364532`.
2. Chọn đặc trưng: tuổi, giới (nhớ 0 = nữ), BMI, vòng eo, SBP, DBP, glucose đói, HbA1c, TC, HDL, TG; bỏ cột trùng đơn vị và cột suy ra. Chia theo người (mỗi dòng đã là một người); nhãn `Incident DM 0/1`. Vì chỉ 373 ca dương (2,41%), báo cáo PR-AUC và khoảng tin cậy; dùng phân tầng theo nhãn khi chia.
3. Nếu muốn có mẫu lớn: tải Rich Healthcare `https://zenodo.org/records/4997196/files/RC%20Health%20Care%20Data-20180820.xlsx?download=1` (28,3 MB), MD5 `b468cc3704b11ba1bd21532451fe2856`. Dùng `Age`, `Gender`, `BMI`, `SBP`, `DBP`, `FPG`, `Cholesterol`, `Triglyceride`, `family histroy of diabetes`; **loại** `FPG of final visit`, `year of followup`, `Diabetes diagnosed during followup`, `site` (không dùng làm đặc trưng); xử lý thiếu HDL/LDL/AST (>40%) bằng cách bỏ cột.
4. Ghi rõ trong báo cáo: hai bộ này là **dân số Nhật/Trung Quốc**, dùng để chứng minh pipeline dự báo mắc mới và so sánh với NHANES; **không** thay cho kiểm định trên người Việt.

## 5. Hạn chế của lần rà soát này

- Không đăng nhập hay đăng ký tài khoản nào, nên quy trình và thời gian duyệt của WHO STEPS, IFLS, CHNS, KNHANES vẫn **chưa xác minh trực tiếp**.
- Không đọc được toàn văn bài NAGALA và BMJ Open (chặn trình duyệt/403); định nghĩa chẩn đoán dựa vào tóm tắt và nguồn thứ cấp.
- Nhiều trang (RAND, KNHANES) trả 403/404 với công cụ tải trang tự động; thông tin về chúng lấy từ kết quả tìm kiếm.
- Chưa đối chiếu số hợp lệ của `b5` và tỷ lệ dương trong STEPS 2021 vì không có microdata.
- Hai tệp Dryad tôi tải vào thư mục tạm của phiên làm việc (ngoài dự án) chỉ để đọc cột và thống kê; không có tệp dữ liệu nào đưa vào dự án.
