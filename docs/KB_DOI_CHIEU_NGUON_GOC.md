# Đối chiếu Knowledge Base với nguồn gốc (ADA 2026, QĐ 5481/QĐ-BYT)

Người lập: Kelp (Knowledge) · Ngày: 2026-11-12 (giờ VN) · Phạm vi: `knowledge/sources_v2.json` (25 đoạn), `knowledge/sources.json` (18 đoạn), `knowledge/graph_entities.json` — số đoạn tại thời điểm đối chiếu; sau khi Pollux áp dụng báo cáo này KB còn 18 + 40 đoạn, 48 thực thể.
Báo cáo này KHÔNG sửa file KB; Atlas áp dụng. Chưa có chuyên gia y tế thẩm định: mọi đề xuất liên quan an toàn người dùng cần Boss/bác sĩ duyệt trước khi đưa vào chatbot.

Quy ước nhãn nguồn: **[GỐC]** = đã đọc trực tiếp văn bản gốc; **[THỨ CẤP]** = trang tóm tắt/bên thứ ba/ghi nhớ; **[KHÔNG ĐỌC ĐƯỢC]**.

---

## 1. Kết quả tra cứu nguồn (ai đọc được gì)

| Nguồn | Trạng thái | Cách đọc | Ghi chú |
|---|---|---|---|
| ADA Standards of Care 2026, Mục 2, 5, 6, 10, 11, 12, 15 và Summary of Revisions (Diabetes Care 49 Suppl 1, 12/2025) | **[GỐC]** — đọc toàn văn trên PMC | `pmc.ncbi.nlm.nih.gov/articles/PMC12690183` (S2), `…PMC12690188` (S5), `…PMC12690178` (S6), `…PMC12690187` (S10), `…PMC12690176` (S11), `…PMC12690177` (S12), `…PMC12690181` (S15), `…PMC12690167` (Summary of Revisions) | Lần trước PMC bị captcha, lần này tải được bằng WebFetch (không dùng đăng ký/đồng ý điều khoản). Mỗi trang rất dài (190–620 nghìn ký tự); chỉ đọc 100.000 ký tự đầu (phần khuyến nghị + bảng) của mỗi mục. Công cụ đọc có qua một bước tóm tắt tự động, nên số liệu trích đã đối chiếu chéo với Summary of Revisions và với QĐ 5481. |
| ADA 2026 "Abridged for Primary Care" (doc26-aint, PMC13696539) | [KHÔNG ĐỌC ĐƯỢC] qua Europe PMC `fullTextXML` (HTTP 500); không cần dùng vì đã có bản đầy đủ | | |
| diabetesjournals.org / professional.diabetes.org | Không thử lại (lần trước 403) | | |
| QĐ 5481/QĐ-BYT (30/12/2020), toàn văn 77 trang | **[GỐC]** — bản PDF ký số 30/12/2020 do BV Đa khoa Bà Rịa lưu | `https://benhviendakhoabaria.vn/sites/default/files/files/tin-tuc/5481_dai_thao_duong_type_2.pdf` | Tải PDF rồi trích chữ bằng Ghostscript. Đã đọc: Phần 2 (chẩn đoán), Bảng 4–5 (mục tiêu), dinh dưỡng/vận động, tăng huyết áp, lipid, biến chứng mắt/thận/chân, hạ đường huyết, DKA/HHS. |
| QĐ 1353/QĐ-BYT (23/02/2021) | **[THỨ CẤP]** — trang caselaw.vn | `https://caselaw.vn/van-ban-phap-luat/366815-…` | Theo tóm tắt: chỉ bổ sung một thành viên biên soạn và đổi câu chữ mục 3 điểm b trang 37 (phác đồ insulin nền–nhanh–trộn cho bệnh nhân nằm viện). Không thay ngưỡng nào liên quan KB. Chưa đọc bản gốc 1353 (PDF syt.bacgiang.gov.vn lỗi kết nối IPv6). |
| URL cũ trong KB `kcb.vn/van-ban/quyet-dinh-so-5481-…html` | **404** (đã xác nhận) | | Nguồn `bytvn-*` trong `sources.json` đang trỏ vào link chết. |
| File `kcb.vn/upload/2005611/20210723/8e4a6b72…_Q-BYT.pdf` (kết quả tìm kiếm hay gặp) | Là **QĐ 3280/QĐ-BYT năm 2011**, đã hết hiệu lực — KHÔNG phải 5481 | | Đừng dùng. |
| NIDDK/CDC/WHO/Vinmec (đối chiếu 43 đoạn) | **[GỐC] cấp trang** — đọc nội dung trang qua WebFetch | | Một số trang NIDDK trả về phiên bản cũ (ghi "Last Reviewed" 2016–2021); ghi chú ở từng dòng. |
| Long Châu, NIDDK `preventing-type-2-diabetes` v.v. | Long Châu: 403; IDF: lỗi chuyển hướng; WHO IRIS 10665/206936: 403; bài Alberti 2009 chỉ đọc được abstract (không đọc được bảng số) | | **[KHÔNG ĐỌC ĐƯỢC]** |

Phiên bản ADA: DOI mới **10.2337/dc26-S002** (S2), **dc26-S005**, **dc26-S006**, **dc26-S010**, **dc26-S011**, **dc26-S012**, **dc26-S015** (Europe PMC ghi chữ thường `dc26-s002`; DOI không phân biệt hoa thường). Nội dung 2026 so với 2025: xem mục 5.

---

## 2. Việc cần sửa, xếp theo mức an toàn người dùng

### Ưu tiên 1 (có thể làm người dùng hiểu sai / nguồn bị sai)

1. **`who-smoking-hypertension-diabetes`**: trang WHO Tobacco fact sheet **không nói gì về đái tháo đường**; không có "gấp 2–3 lần", "nicotine làm nặng kháng insulin", "huyết áp < 130/80". Các số này là khẳng định không có căn cứ trong nguồn đã trích. Cạnh `hut-thuoc → dtd-typ2` trong đồ thị đang dựa vào nguồn này. Đề xuất: bỏ đoạn hoặc viết lại chỉ với ý có nguồn (ADA 2026 S5, rec 5.40: đánh giá và tránh thuốc lá/thuốc lá điện tử ở mọi người đái tháo đường; ADA S10 cho mục tiêu huyết áp). Đổi nguồn cạnh đồ thị.
2. **Link chết/nguồn không chứa nội dung** (người dùng bấm vào sẽ không thấy gì): `bytvn-diagnosis-guidelines`, `bytvn-hyperglycemia-complications` (kcb.vn 404), `ada-hypoglycemia-emergency` (diabetes.org/…/hypoglycemia 404), `ada-foot-care` (diabetes.org/…/foot-care 404), `cdc-chronic-complications` (cdc.gov/diabetes/about/complications.html 404), `ada-nutrition-guidelines` (diabetes.org/food-nutrition tồn tại nhưng trang không có Plate Method). Thay URL: QĐ 5481 → link PDF Bà Rịa ở mục 1; hạ đường huyết → ADA dc26-S006 + NIDDK; đĩa ăn → CDC `diabetes-meal-planning.html` (đã xác nhận đúng).
3. **Ngưỡng huyết áp và LDL ghi theo ADA, Việt Nam khác** (`kb2-muc-tieu-kiem-soat`): KB nêu < 130/80 và "LDL do bác sĩ đặt". QĐ 5481 Bảng 4: huyết áp < 140/90 (< 130/80 nếu có biến chứng thận hoặc nguy cơ tim mạch xơ vữa cao); LDL < 100 mg/dL (chưa có bệnh tim mạch), < 70 (đã có), < 50 hoặc thấp hơn (nguy cơ rất cao); TG < 150; HDL > 40 nam / > 50 nữ. ADA 2026: huyết áp < 130/80 (rec 10.4), khuyến khích SBP < 120 ở nguy cơ tim mạch/thận cao (ESPRIT); LDL < 70 mg/dL (phòng ngừa nguyên phát nguy cơ cao, tuổi 40–75, rec 10.20) và < 55 mg/dL (đã có ASCVD, rec 10.27). Đề xuất: thêm một câu "Hướng dẫn của Bộ Y tế VN (QĐ 5481) dùng ... ; ADA dùng ...; bác sĩ điều trị quyết định" thay vì chỉ ghi ADA.
4. **Sàng lọc: tuổi 35 (ADA) so với 45 (Bộ Y tế VN)** (`kb2-ai-nen-sang-loc`, `tuoi-cao` trong đồ thị, `cdc-risk-factors`, `bytvn`): ADA 2026 rec 2.12b: bắt đầu từ 35 tuổi. QĐ 5481 mục 1.2c: "Tất cả mọi người từ 45 tuổi trở lên"; CDC cũng ghi 45. Hiện KB tự mâu thuẫn (v2 nói 35, v1 nói 45). Đề xuất: viết "ADA 2026: từ 35 tuổi; Bộ Y tế VN (QĐ 5481): từ 45 tuổi; người thừa cân BMI ≥ 23 kèm yếu tố nguy cơ thì sàng lọc ở mọi tuổi (cả hai hướng dẫn đồng ý)". Yếu tố nguy cơ tăng huyết áp: ADA ≥ 130/80 hoặc đang điều trị; VN ≥ 140/90 hoặc đang điều trị. Lặp lại khi bình thường: ADA ≥ mỗi 3 năm; VN mỗi 1–3 năm. Tiền ĐTĐ kiểm tra hằng năm (ADA 2026, khớp KB).
5. **Rượu bia: "1 đơn vị" khác định nghĩa** (`kb2-ruou-bia`): KB ghi 1 đơn vị ≈ 14 g cồn (350 ml bia, 150 ml vang, 45 ml mạnh). ADA 2026 (rec 5.18) chỉ cho bằng oz: 12 oz bia, 5 oz vang, 1.5 oz rượu mạnh; **không ghi "14 g"**. QĐ 5481 (mục 5, đồ uống có cồn): "không quá 1–2 đơn vị, 1 đơn vị = 10 g cồn ≈ 120 ml vang, 300 ml bia, 30 ml rượu mạnh" (không tách theo giới). Đề xuất: ghi đúng cả hai (ADA ≤ 1/ngày nữ, ≤ 2/ngày nam; VN 1–2 đơn vị, 10 g cồn), nêu quy đổi theo ml của VN để người dùng Việt dễ áp dụng, bỏ con số 14 g hoặc ghi "ước tính theo chuẩn Mỹ". Ý "uống rượu có thể gây hạ đường huyết muộn" khớp ADA rec 5.19 và QĐ 5481.
6. **`bytvn-hyperglycemia-complications`**: QĐ 5481 (bảng tiêu chuẩn DKA/HHS): DKA đường huyết **≥ 14,0 mmol/L** (KB ghi > 13,9, chênh nhỏ); HHS **> 33,3 mmol/L** (khớp). Cần thêm cảnh báo: DKA vẫn có thể xảy ra khi đường huyết không quá cao (ví dụ đang dùng thuốc SGLT2, mang thai: ADA S6 nêu DKA "euglycemic" khi < 200 mg/dL ở thai kỳ) — nếu không, người dùng thấy đường huyết 200–250 mà có buồn nôn, thở nhanh có thể chủ quan. Đề xuất: bổ sung câu "đường huyết không quá cao không loại trừ DKA".
7. **`kb2-ha-duong-huyet-15-15`** (an toàn, nội dung chính xác nhưng nguồn trích chưa chứa đủ): xem bảng mục 3.

### Ưu tiên 2 (lệch nhỏ, nên sửa trích dẫn/diễn đạt)

- `kb2-van-dong`: "3 phút mỗi 30 phút" **không có** trong văn bản ADA 2026 đã đọc (rec 5.34 và nội dung chỉ nói ngắt ngồi lâu "ít nhất mỗi 30 phút" bằng đứng/đi nhẹ). QĐ 5481: tránh ngồi lâu, mỗi 20–30 phút đứng dậy đi lại. Đề xuất sửa còn "đứng dậy vận động nhẹ ít nhất mỗi 30 phút". Các số 150 phút/tuần, ≥ 3 ngày, không nghỉ quá 2 ngày liên tiếp, kháng lực 2–3 buổi: **khớp ADA 2026 rec 5.36–5.37**. "Ăn nhẹ nếu glucose trước tập < 90 mg/dL": khớp ADA S5. VN: tập 5 ngày/tuần, đi bộ 150 phút (30 phút/ngày), kháng lực 2–3 lần/tuần.
- `kb2-tien-dai-thao-duong`: "giảm 7% cân + 150 phút/tuần → giảm 58% sau ~3 năm" **không có** trên trang NIDDK đã trích (trang chỉ nói giảm 5–7% cân nặng có lợi). Số 58% là kết quả DPP (Knowler, NEJM 2002) — chưa đọc bài gốc trong lần này, nên cần trích bài gốc hoặc bỏ. ADA 2026 rec 3.3 và 5.12 nêu 5–7%.
- `kb2-bien-chung-than`: "UACR < 30 mg/g" và "eGFR < 60" khớp ADA 2026 S11 (UACR A1 < 30; A2 30–< 300; A3 ≥ 300) nhưng **trang NIDDK đã trích (Last Reviewed 02/2017) không có**; ý "bất thường kéo dài trên 3 tháng mới chẩn đoán" không thấy trong đoạn ADA S11 đã đọc (ADA chỉ nói albumin niệu cần 2 trong 3 mẫu bất thường trong 3–6 tháng) — định nghĩa ≥ 3 tháng đến từ KDIGO, chưa đọc nguồn này. Tần suất ít nhất mỗi năm: khớp ADA rec 11.1a (típ 1 từ 5 năm, mọi người típ 2) và QĐ 5481 (hằng năm; 2 lần/năm nếu albumin niệu > 30 mg/g hoặc eGFR < 60). Đề xuất: đổi URL sang dc26-S011 và thêm KDIGO nếu giữ "3 tháng".
- `kb2-bien-chung-mat`: ADA rec 12.3–12.5: típ 2 khám ngay khi chẩn đoán; típ 1 sau 5 năm; mỗi năm, giãn 1–2 năm nếu nhiều lần bình thường và đường huyết đạt mục tiêu — **khớp KB**. Trang NIDDK (05/2017) chỉ nói hằng năm. QĐ 5481: típ 2 khám ngay, sau đó mỗi 1–2 năm (dễ dãi hơn mặc định "hằng năm" của KB); típ 1 sau 5 năm (đôi khi 3 năm); thai phụ ĐTĐ có sẵn khám ngay khi biết có thai (ADA: trước thai kỳ và trong 3 tháng đầu); ĐTĐ thai kỳ không cần khám mắt (cả hai đồng ý). Không xung đột nguy hiểm.
- `kb2-than-kinh-ban-chan`: khám bàn chân toàn diện hằng năm, monofilament 10 g: khớp ADA rec 12.18, 12.23. ADA 2026 có phân tầng nguy cơ loét (mỗi 1–3 / 3–6 / 6–12 tháng / hằng năm) — KB chưa có, có thể thêm. QĐ 5481: kiểm tra bàn chân toàn diện ít nhất mỗi năm, và **kiểm tra bàn chân ở mỗi lần khám**. Trang NIDDK (01/2017) không nhắc monofilament nhưng nhắc "không ngâm chân" (lý do da khô) chứ **không** nhắc "không ngâm nước nóng" như KB; cần chỉnh: "không ngâm chân; không dùng túi sưởi/chai nước nóng".
- `kb2-thai-ky`: trang NIDDK (05/2017) chỉ chứng minh mốc 24–28 tuần. Các ý còn lại khớp ADA S15 rec 15.30 (OGTT 75 g sau sinh 4–12 tuần) và 15.31 (sàng lọc suốt đời mỗi 1–3 năm), và QĐ 5481 mục 1.3. **Mới ở 2026**: A1C 6–12 tháng sau sinh chỉ bổ sung, không thay OGTT (chỉ cho người không thể/không muốn làm OGTT). Ngưỡng 92/180/153 đã khớp ADA 2026 và QĐ 5481 (VN dùng phương pháp một bước).
- `kb2-hba1c-la-gi`: NIDDK (bản đọc được ghi 04/2018) nói HbA1c phản ánh **3 tháng** (KB ghi 2–3 tháng, ADA thường dùng "2–3 tháng": chấp nhận); không nêu "mang thai" là yếu tố làm HbA1c sai (nêu "không dùng chẩn đoán ĐTĐ thai kỳ"); không nêu riêng thalassemia/HbE (chỉ nói biến thể hemoglobin ở người gốc Đông Nam Á — nên bỏ "HbE" hoặc nêu nguồn khác). ADA 2026 S2/S15 nêu: thiếu máu, biến thể hemoglobin, thay đổi vòng đời hồng cầu, thiếu sắt (làm A1C cao) → trích ADA.
- `kb2-tieu-chuan-chan-doan-so`: bốn tiêu chuẩn và nhắc lại hai kết quả **khớp ADA 2026 (Bảng 2.1)** và QĐ 5481 mục 1.1 (tiêu chí a–c cần hai kết quả cùng mẫu hoặc hai thời điểm; tiêu chí d chỉ cần một lần). Ghi chú "WHO đặt IFG từ 110 mg/dL": trang WHO diabetes (đọc 12/11/2026) không có con số glucose nào, nên chưa xác nhận được; con số 110 (WHO/IDF 2006) chỉ từ ghi nhớ — cần nguồn. QĐ 5481 **không định nghĩa tiền ĐTĐ** trong phần đã đọc, nên ngưỡng 100–125 / 140–199 / 5,7–6,4% chỉ có từ ADA (đọc được trong ADA 2026 Bảng 2.2). Đổi URL sang dc26-S002.
- `kb2-nghiem-phap-ogtt`: ADA 2026 rec 2.14: ăn ≥ 150 g carbohydrate/ngày trong 3 ngày trước; QĐ 5481: 150–200 g/ngày, hòa 75 g glucose trong 250–300 ml nước, uống trong 5 phút. KB nói "ăn bình thường" — nên thêm "ít nhất 150 g tinh bột/ngày".
- `kb2-ngay-om`: số liệu CDC (đo mỗi 4 giờ, ~50 g carbohydrate mỗi 4 giờ, không giữ được nước > 4 giờ, nôn/tiêu chảy > 6 giờ, đường huyết < 60 mg/dL, sốt > 101°F ≈ 38,3°C kéo dài 24 giờ) **khớp trang CDC (cập nhật 05/2024)**. Ý "metformin/SGLT2 có thể cần tạm ngưng" **không có trên trang CDC**; ADA 2026 Summary: S6 bổ sung tiêu chí tạm ngừng một số nhóm thuốc khi ốm — nên trích dc26-S006 cho ý này (chưa đọc chi tiết mục đó). Lưu ý an toàn: KB đã nói đúng "luôn hỏi bác sĩ".
- `kb2-theo-doi-tai-nha`: NIDDK nói CGM "ước lượng" glucose dịch kẽ, có báo động, nên so với que thử khi nghi ngờ/đổi liều insulin/có cảnh báo; **không nói** thời gian trong khoảng, độ trễ, kỹ thuật chích đầu ngón (rửa tay, bên cạnh đầu ngón) — các ý này cần trích nguồn khác (ADA S7 chưa đọc).
- `kb2-dia-an`: đĩa 9 inch (≈ 23 cm), 1/2 rau không tinh bột, 1/4 đạm, 1/4 tinh bột, sữa/trái cây/đậu tính vào phần tinh bột: **khớp CDC**. "Ăn rau và đạm trước tinh bột" và "người dùng insulin/thuốc kích thích tiết insulin không nên bỏ bữa" **không có trên trang CDC** — đổi nguồn hoặc bỏ.
- `kb2-tinh-bot-chi-so-duong-huyet`: 1 khẩu phần tinh bột = 15 g: **khớp CDC**. Trang CDC **không bàn về GI**. ADA 2026 S5: không có khuyến nghị số về GI/GL, bằng chứng chưa nhất quán; ưu tiên tinh bột ít chế biến giàu xơ, ≥ 14 g xơ/1.000 kcal (rec 5.24). Câu "tổng lượng tinh bột quan trọng hơn một con số GI" phù hợp tinh thần ADA nhưng nên trích dc26-S005 thay vì CDC.
- `kb2-tim-mach`: trang CDC (05/2024) chỉ xác nhận "nguy cơ bệnh tim gấp đôi", ABC (huyết áp **< 140/90** theo CDC) và bỏ thuốc lá. **Không có** trên trang: xuất hiện sớm hơn, nguyên nhân tử vong hàng đầu, danh sách dấu hiệu cấp cứu. Các ý này đúng về mặt kiến thức phổ biến nhưng cần nguồn khác (ADA S10 / AHA) — chưa đọc trong lần này. Dấu hiệu cấp cứu giữ lại vì an toàn, ghi rõ nguồn.
- `kb2-suc-khoe-tinh-than`: CDC (05/2024) xác nhận trầm cảm gấp 2–3 lần, lo âu nhiều hơn 20%, lo âu giống hạ đường huyết nên đo đường huyết, diabetes distress. **Không có** "ít nhất 7 giờ/đêm". ADA 2026 rec 5.56–5.57 chỉ khuyến cáo sàng lọc/khuyên thói quen ngủ, không ghi số giờ trong đoạn đã đọc. Bỏ hoặc trích nguồn giấc ngủ riêng. ADA 2026 thêm: sàng lọc lo âu ít nhất hằng năm (5.46), sợ hạ đường huyết (5.47).
- `kb2-chi-so-mo-mau`: bài Alberti 2009 (Circulation 120:1640) — chỉ đọc được abstract: xác nhận "3 trong 5 tiêu chí" và "ngưỡng vòng eo theo quốc gia/khu vực"; **chưa đọc bảng số** (TG ≥ 150, HDL < 40/50, glucose ≥ 100, huyết áp ≥ 130/85, vòng eo). Theo ghi nhớ (chưa kiểm chứng): bảng ngưỡng vòng eo theo dân tộc — người Nam Á/Nhật ≥ 90 nam, ≥ 80 nữ; người Trung Quốc ≥ 85 nam, ≥ 80 nữ. Vậy câu "người châu Á ≥ 90/≥ 80" là đơn giản hóa; với người Việt, QĐ 5481 (mục 5.2.2) dùng **vòng eo < 90 cm nam, < 80 cm nữ** — khớp KB. Đề xuất trích QĐ 5481 cho vòng eo.
- `kb2-beo-bung-chau-a`: WHO IRIS (10665/206936) trả 403 [KHÔNG ĐỌC ĐƯỢC]; bảng BMI châu Á (18,5–22,9 bình thường; 23–24,9 thừa cân/nguy cơ; ≥ 25 béo phì) chỉ từ ghi nhớ về khuyến nghị Asia-Pacific 2000. QĐ 5481 chỉ dùng BMI ≥ 23 như ngưỡng thừa cân/béo phì để sàng lọc (mục 1.2a) và không có bảng phân loại BMI đầy đủ trong phần đã đọc; vòng eo khớp. ADA 2026 dùng ≥ 23 cho người gốc Á (Bảng 2.5, đã đọc). Đề xuất: chỉ khẳng định "≥ 23 là ngưỡng sàng lọc ở người gốc Á (ADA, Bộ Y tế VN)"; câu "≥ 25 là béo phì" ghi là phân loại Asia-Pacific và cần nguồn đọc được.
- `kb2-doi-don-vi`: URL trích (dc25-S002) không chứa hệ số 18 / 38,7 / 88,6 (kiến thức đổi đơn vị chung). Đề xuất bỏ link ADA hoặc dẫn nguồn đổi đơn vị riêng. Các giá trị 5,6/7,0/10,0/11,1/3,9/3,0 và 6,5% = 48, 7% = 53 mmol/mol khớp ADA và QĐ 5481.
- `kb2-chi-so-gan-than`: trang NIDDK NAFLD (04/2021) dùng "NAFLD", không dùng MASLD, không nhắc ALT/kháng insulin; chỉ nói ĐTĐ típ 2 làm tăng nguy cơ. ADA 2026 Summary: thêm MASLD (Hình 4.1–4.3) và FIB-4 > 2,67 thì chuyển chuyên khoa gan. Đổi sang ADA S4.
- `kb2-typ1-typ2-khac-nhau`: CDC típ 1 (cập nhật 11/09/2026) xác nhận tự miễn, mọi lứa tuổi, insulin hằng ngày, chưa biết cách phòng; **không nêu thuốc trì hoãn khởi phát** và không dùng chữ "suốt đời"; "típ 2 chiếm 90–95%" suy ra từ "típ 1 ~ 5–10%" (QĐ 5481 ghi 90–95%). ADA 2026 Rec 2.8–2.9 (giai đoạn kháng thể) có thể làm nguồn cho ý trì hoãn.
- `kb2-hieu-ket-qua-mo-hinh`: tài liệu nội bộ, không thuộc phạm vi đối chiếu.

### Phần ADA 2026 xác nhận ĐÚNG (không cần sửa số)

- Chẩn đoán: FPG ≥ 126, 2 giờ OGTT ≥ 200, A1C ≥ 6,5%, ngẫu nhiên ≥ 200 + triệu chứng/khủng hoảng; tiền ĐTĐ 100–125 / 140–199 / 5,7–6,4% (S2, Bảng 2.1–2.2).
- Mục tiêu: A1C < 7%, glucose trước ăn 80–130, đỉnh sau ăn < 180 mg/dL; CGM TIR > 70%, < 70 mg/dL < 4%, < 54 mg/dL < 1% (S6, rec 6.3, Bảng 6.2).
- Hạ đường huyết: mức 1 < 70 và ≥ 54; mức 2 < 54; mức 3 cần người khác giúp (S6, Bảng 6.4); xử trí thường 15 g carbohydrate nhanh, đo lại sau 15 phút, ưu tiên glucose nguyên chất, glucagon cho người dùng insulin (6.16), mức 2–3 phải xem lại điều trị (6.19). Mới 2026: rec 6.17 đưa glucose uống vào bộ sơ cứu.
- GDM: 92/180/153 mg/dL (S2/S15).
- Sau sinh 4–12 tuần, suốt đời mỗi 1–3 năm (15.30–15.31).
- Hoạt động thể lực, rượu bia theo giới (5.18, 5.36–5.37).

---

## 3. `knowledge/sources_v2.json`: bảng id | nhận định | nguồn gốc nói gì | đề xuất

Ký hiệu nhận định: **Đúng** (khớp nguồn gốc), **Đúng một phần**, **Không có trong nguồn đã trích**, **Cần VN-note** (đúng theo ADA, VN khác).

| id | Nhận định | Nguồn gốc nói gì (URL / mục) | Đề xuất sửa |
|---|---|---|---|
| kb2-hba1c-la-gi | Đúng một phần | NIDDK a1c-test (Last Reviewed 04/2018): <5,7 / 5,7–6,4 / ≥6,5; không cần nhịn; "3 tháng"; biến thể Hb ở người gốc Đông Nam Á, thiếu sắt, bệnh thận, bệnh gan; không dùng chẩn đoán ĐTĐ thai kỳ. ADA S2 (PMC12690183) về hạn chế A1C. https://www.niddk.nih.gov/health-information/diagnostic-tests/a1c-test | Bỏ "HbE"/"mang thai" khỏi nguồn NIDDK hoặc trích ADA S2/S15; thêm URL ADA. |
| kb2-tieu-chuan-chan-doan-so | Đúng; Cần VN-note | ADA dc26-S002 Bảng 2.1 (PMC12690183); QĐ 5481 mục 1.1 (PDF Bà Rịa, tr.9). Hai kết quả: cùng mẫu hoặc hai thời điểm (a, b, c); d chỉ một lần. | Đổi URL dc26-S002; bỏ hoặc nguồn hóa "WHO 110"; ghi QĐ 5481 không định nghĩa tiền ĐTĐ. |
| kb2-tien-dai-thao-duong | Đúng một phần | NIDDK (03/2025): 100–125 / 140–199 / 5,7–6,4; giảm 5–7% cân; khám lại hằng năm; KHÔNG có 58%/150 phút/3 năm. https://www.niddk.nih.gov/health-information/diabetes/overview/what-is-diabetes/prediabetes-insulin-resistance | Bỏ hoặc trích bài DPP gốc (NEJM 2002) cho 58%; thêm ADA 3.3. |
| kb2-doi-don-vi | Đúng (kiến thức chung) | Không có trong dc25-S002. Các cặp giá trị khớp ADA/QĐ 5481. | Bỏ link ADA hoặc đổi nguồn. |
| kb2-nghiem-phap-ogtt | Đúng; thiếu chi tiết | NIDDK tests-diagnosis; ADA rec 2.14 (≥150 g carbohydrate/ngày × 3 ngày); QĐ 5481 tr.9 (150–200 g; 75 g/250–300 ml/5 phút). | Thêm "≥150 g tinh bột/ngày". |
| kb2-ai-nen-sang-loc | Cần VN-note | ADA S2 Bảng 2.5, rec 2.12: BMI ≥25 hoặc ≥23 người gốc Á + yếu tố nguy cơ; từ 35 tuổi; bình thường lặp ≥ mỗi 3 năm; tiền ĐTĐ hằng năm; sau ĐTĐ thai kỳ mỗi 1–3 năm. QĐ 5481 mục 1.2: BMI ≥23 + yếu tố nguy cơ; ≥45 tuổi; lặp 1–3 năm; HA ≥140/90; HDL <35 và/hoặc TG >250. | Thêm câu 45 tuổi của VN và HA 140/90; đổi URL dc26-S002. |
| kb2-beo-bung-chau-a | Đúng một phần; nguồn gốc không đọc được | WHO IRIS 403. QĐ 5481 mục 5.2.2: vòng eo <80 nữ, <90 nam (đúng KB). Không có bảng BMI. | Giữ vòng eo (trích QĐ 5481); hạ mức chắc chắn của "≥25 béo phì". |
| kb2-muc-tieu-kiem-soat | Cần VN-note (ưu tiên 1) | ADA S6 rec 6.3, Bảng 6.2; S10 rec 10.4, 10.20, 10.27. QĐ 5481 Bảng 4–5 (tr.18–19). Người cao tuổi: ADA <8% (phức tạp); VN <7,5 / <8,0 / <8,5% theo tình trạng; VN cho phép 7,5–8% ở người lớn tuổi/nhiều bệnh. | Xem mục 2 điểm 3. |
| kb2-ha-duong-huyet-15-15 | Đúng; cần nguồn đầy đủ hơn | ADA S6 Bảng 6.4 + rec 6.15–6.19. QĐ 5481 Phần 6 (tr.40): 15–20 g glucose, đo lại 15 phút, sau đó ăn nhẹ; mức 2 trở lên cần glucagon (nếu có); tiêm tĩnh mạch 50 ml glucose 50% (~25 g) tại cơ sở y tế. NIDDK (07/2021) chỉ nêu <70, 15–20 g, ví dụ 4 viên glucose/½ cốc nước ép/1 thìa đường, soda thường, glucagon; KHÔNG nêu <54, acarbose, hay "không cho ăn uống qua miệng". | Thêm ADA dc26-S006 và QĐ 5481 vào nguồn; giữ nguyên nội dung xử trí. Giữ câu "không cho ăn uống khi bất tỉnh" (an toàn, chuẩn sơ cứu) ghi rõ nguồn riêng. |
| kb2-ngay-om | Đúng một phần | CDC managing-sick-days (05/2024): số liệu khớp; không nêu metformin/SGLT2. | Trích ADA S6 cho ý tạm ngừng thuốc. |
| kb2-typ1-typ2-khac-nhau | Đúng một phần | CDC about-type-1 (09/2026). | Xem mục 2. |
| kb2-thai-ky | Đúng; sửa nguồn | NIDDK gestational (05/2017) chỉ có 24–28 tuần. ADA S15 15.30–15.31; QĐ 5481 mục 1.3. | Thêm ADA dc26-S015, QĐ 5481; thêm ý A1C 6–12 tháng sau sinh chỉ bổ sung. |
| kb2-bien-chung-than | Đúng một phần | NIDDK (02/2017) chỉ có "hằng năm". ADA S11 rec 11.1a; QĐ 5481 Biến chứng thận. | Xem mục 2. |
| kb2-bien-chung-mat | Đúng; Cần VN-note nhỏ | ADA S12 rec 12.3–12.5; QĐ 5481 (típ 2 ngay + mỗi 1–2 năm). | Thêm VN-note. |
| kb2-than-kinh-ban-chan | Đúng một phần | ADA S12 rec 12.17–12.25 và Bảng 12.1; QĐ 5481 (hằng năm + mỗi lần khám). | Sửa "ngâm nước nóng" thành "không ngâm chân"; thêm phân tầng. |
| kb2-tim-mach | Đúng một phần | CDC (05/2024): nguy cơ gấp đôi; ABC; HA <140/90. | Thêm nguồn cho các ý còn lại. |
| kb2-dia-an | Đúng một phần | CDC meal-planning: đĩa 9 inch. | Bỏ/nguồn hóa hai ý không có. |
| kb2-tinh-bot-chi-so-duong-huyet | Đúng một phần | CDC choosing-healthy-carbs: 15 g/khẩu phần; ADA S5: không số GI cụ thể, ≥14 g xơ/1.000 kcal. | Đổi nguồn GI sang dc26-S005. |
| kb2-van-dong | Đúng một phần | Xem mục 2. ADA rec 5.34–5.37; QĐ 5481. | Bỏ "3 phút". |
| kb2-ruou-bia | Cần VN-note (ưu tiên 1) | ADA rec 5.18–5.19; QĐ 5481 mục dinh dưỡng f. | Xem mục 2. |
| kb2-theo-doi-tai-nha | Đúng một phần | NIDDK CGM (06/2023). | Thêm nguồn ADA S7 cho phần còn lại. |
| kb2-suc-khoe-tinh-than | Đúng một phần | CDC mental-health (05/2024). | Bỏ "7 giờ" hoặc nguồn khác. |
| kb2-chi-so-mo-mau | Đúng một phần | Alberti abstract; QĐ 5481 Bảng 4 (HDL >40/>50, TG <150). ADA rec 10.15: TG ≥150, HDL <40 nam / <50 nữ. | Trích ADA S10 + QĐ 5481 cho HDL/TG. |
| kb2-chi-so-gan-than | Đúng một phần | NIDDK NAFLD (04/2021). | Đổi sang ADA S4. |
| kb2-hieu-ket-qua-mo-hinh | Nội bộ | Không áp dụng | Giữ. |

---

## 4. `knowledge/sources.json` (18 đoạn)

Độ tin cậy nguồn (thang T1–T5 của skill `researching-technical-sources`): WHO/CDC/NIDDK/ADA = T1; Vinmec = T3–T4 (bệnh viện tư, có bác sĩ chuyên khoa duyệt nhưng là nội dung thương mại); Long Châu = T4 (chuỗi nhà thuốc, bán sản phẩm).

| id | Nhận định | Nguồn gốc nói gì | Đề xuất sửa |
|---|---|---|---|
| who-diabetes-overview | Đúng | WHO diabetes fact sheet (trang đọc được đề ngày 11/11/2026): "chronic disease ... pancreas does not produce enough insulin ... or cannot use insulin effectively", tổn thương thần kinh và mạch máu. https://www.who.int/news-room/fact-sheets/detail/diabetes | Trường `date` trong KB (2023) khác ngày trang hiện tại; cập nhật `date` thành ngày truy cập. |
| who-diabetes-types | Đúng một phần | Trang WHO không dùng chữ "prediabetes" (gọi IGT/IFG là "intermediate conditions"); không nói "không phải một típ". | Nêu "IGT/IFG là trạng thái trung gian" hoặc dẫn ADA S2. |
| cdc-classic-symptoms | Đúng một phần | CDC symptoms (05/2024): tiểu nhiều, khát/đói tăng, sụt cân không chủ ý, mệt, cáu gắt, nhìn mờ, nhiễm trùng tiết niệu/nấm; típ 2: vết thương lâu lành, sạm da, tê bì. Không có "tứ chứng", "đặc biệt vào ban đêm", "khô ngứa da". | Bỏ các chi tiết không có trên trang. |
| cdc-risk-factors | Đúng một phần | CDC risk-factors: tuổi ≥45, vận động <3 lần/tuần, ĐTĐ thai kỳ hoặc sinh con >9 pound (~4,1 kg). **Không nêu huyết áp 140/90 hay rối loạn lipid.** | Bỏ vế huyết áp/lipid khỏi đoạn này hoặc trích QĐ 5481/ADA. |
| cdc-prevention-lifestyle | Đúng | NIDDK preventing-type-2 (Last Reviewed 11/2016): giảm 5–7% cân, ≥30 phút × 5 ngày/tuần. | Có thể thêm số 5–7%. Trang cũ (2016); cân nhắc ADA S3/S5. |
| bytvn-diagnosis-guidelines | Đúng; **URL chết** | QĐ 5481 mục 1.1 (tr.9): đúng 4 tiêu chí; a, b, c cần lặp lại; d một lần. | Đổi URL sang PDF Bà Rịa. |
| ada-nutrition-guidelines | Nguồn không chứa nội dung | diabetes.org/food-nutrition ("How to Eat Healthy") không có Plate Method. Nội dung đúng theo CDC. | Đổi sang CDC diabetes-meal-planning. |
| who-physical-activity | Đúng một phần | Trang WHO (04/11/2026): ≥150 phút cường độ vừa/tuần. Bản đọc được không ghi 150–300, 75–150, "không nghỉ >2 ngày", "độ nhạy insulin". | Số 300/75–150 có trong hướng dẫn WHO 2020 về vận động (chưa đọc lần này); trích nguồn đó hoặc dùng ADA rec 5.36. |
| ada-hypoglycemia-emergency | **URL chết (404)** | Nội dung khớp ADA S6/NIDDK (xem trên). | Đổi URL. |
| bytvn-hyperglycemia-complications | Đúng; **URL chết** | QĐ 5481 (tr.~46): DKA ≥14,0 mmol/L; HHS >33,3. | Xem mục 2 điểm 6. |
| cdc-chronic-complications | **URL chết (404)** | — | Tìm URL mới trên cdc.gov/diabetes (chưa xác định) hoặc dùng NIDDK/ADA. |
| ada-foot-care | **URL chết (404)** | Nội dung chung khớp NIDDK foot-problems (01/2017): khám chân mỗi ngày, không đi chân trần, không tự cắt chai. Chưa kiểm chứng "cắt móng thẳng", "kiểm tra nhiệt độ nước bằng cùi chỏ". | Đổi URL sang NIDDK/ADA S12. |
| idf-blood-glucose-monitoring | Không đọc được | idf.org lỗi chuyển hướng; <7% khớp ADA và QĐ 5481. | Đổi sang ADA S6 / QĐ 5481. |
| who-smoking-hypertension-diabetes | **Không có căn cứ trong nguồn** | WHO Tobacco (26/06/2026) không nói về đái tháo đường. | Ưu tiên 1, xem mục 2. |
| vinmec-diabetes-overview | Đúng (diễn đạt thận trọng) | Vinmec "Tổng quan về bệnh đái tháo đường" (cập nhật 22/07/2024), cố vấn chuyên môn Bác sĩ CKII Nguyễn Xuân Thắng. Trang còn nêu sàng lọc BMI ≥23, từ 45 tuổi, ngưỡng chẩn đoán/tiền ĐTĐ khớp ADA/QĐ 5481. | Giữ; gắn nhãn "nguồn thương mại, tham khảo". |
| vinmec-type2-signs | Chưa đọc trang | Không mở URL này trong lần này. | Đọc và đánh giá lại nếu giữ. |
| longchau-diabetes-faq | Không đọc được (403) | Chuỗi nhà thuốc thương mại. | Nên thay bằng BYT/ADA/CDC; nếu giữ, nhãn nguồn thương mại. |
| who-types-prevention-vn | Đúng | WHO diabetes (11/2026): ăn uống, ≥150 phút/tuần, cân nặng hợp lý, không hút thuốc. | `date` 2026-11-03 không khớp trang; cập nhật. |

---

## 5. ADA 2026 so với 2025 (những chỗ ảnh hưởng KB)

Nguồn: Summary of Revisions (PMC12690167), cộng với các bảng đã đọc.

- Không thấy thay ngưỡng chẩn đoán/tiền ĐTĐ (S2) hay mục tiêu A1C/glucose (S6) trong các đoạn KB trích.
- S2: Rec 2.8 tách 2.8a/2.8b; Rec 2.9 mới (kháng thể IA-2 đơn lẻ); Recs 2.18–2.22 mới (thuốc corticoid, ức chế điểm kiểm soát miễn dịch, PI3Kα); sàng lọc ĐTĐ thai kỳ gộp vào Rec 2.31b, nội dung chuyển sang S15.
- S5: Rec 5.12 (≥5–7% giảm cân); 5.34 (tăng vận động); 5.40 (thuốc lá/vape); 5.46 (lo âu hằng năm); 5.47 (sợ hạ đường huyết); 5.56 (giấc ngủ). Rượu bia và số phút vận động giữ nguyên trong đoạn đã đọc.
- S6: Rec 6.17 mới (glucose uống trong bộ sơ cứu); điều kiện tạm ngừng thuốc khi ốm; mở rộng DKA ngoại trú; Hình 6.1 có mục tiêu CGM cá thể hóa.
- S10: Rec 10.4 khuyến khích SBP < 120 ở nguy cơ cao (thử nghiệm ESPRIT); Rec 10.10 ACEi/ARB mạnh khi albumin niệu nặng và/hoặc eGFR < 60; 10.32 không thêm fibrate/niacin/omega-3 vào statin.
- S11: Rec 11.9 mới (SGLT2i + finerenone đồng thời khi UACR ≥100 mg/g, eGFR 30–90); 11.11a/b mới.
- S12: thêm Ipswich touch test; phân tầng nguy cơ chân; GLP-1 RA và mắt.
- S15: Rec 15.24 ngưỡng điều trị tăng huyết áp thai kỳ 140/90; A1C sau sinh chỉ bổ sung.
- Hạn chế: chưa đọc song song bản 2025, nên "không đổi" chỉ suy ra từ Summary of Revisions.

---

## 6. `graph_entities.json`

Các trường `threshold`/`note` kiểm được:

| Mục (dòng) | Giá trị | Nhận định | Đề xuất |
|---|---|---|---|
| ngưỡng glucose đói ≥126, OGTT ≥200, A1C ≥6,5, ngẫu nhiên ≥200 (635–656) | Đúng | ADA S2 + QĐ 5481 | Giữ |
| tiền ĐTĐ 100–125, "WHO dùng 110–125" (663) | ADA đúng; WHO chưa xác nhận | trang WHO không có số | Bỏ "WHO 110–125" hoặc nguồn hóa |
| 2 giờ 140–199; A1C 5,7–6,4 (670, 677) | Đúng | ADA Bảng 2.2 | Giữ |
| GDM 92/180/153 "chỉ cần một giá trị" (684) | Đúng | ADA S2; QĐ 5481 | Giữ |
| hạ đường huyết mức 1/2 (692) | Đúng | ADA Bảng 6.4; QĐ 5481 | Giữ |
| UACR <30 mg/g; eGFR <60 kéo dài ≥3 tháng (741, 748) | UACR đúng; "≥3 tháng" chưa có nguồn đọc được | ADA S11 không nêu thời gian | Thêm KDIGO hoặc bỏ |
| mắt (755), chân (762) | Đúng | ADA S12; QĐ 5481 | Thêm VN-note mắt (1–2 năm) |
| HbA1c <7% (769) | Đúng | ADA + QĐ 5481 | Giữ |
| DPP 58% (776) | Không có trong nguồn NIDDK đã trích | Xem mục 2 | Nguồn hóa hoặc bỏ |
| 15–20 g đường nhanh (819) | Đúng | NIDDK; QĐ 5481 | Giữ; ADA ghi "thường 15 g" |
| BMI ≥23/≥25; vòng eo ≥90 nam/≥80 nữ (565, 572) | Vòng eo khớp QĐ 5481; BMI ≥23 khớp, ≥25 chưa kiểm | | Xem mục 2 |
| ADA sàng lọc từ 35 tuổi (591) | Đúng theo ADA; VN 45 | | Thêm VN |
| HDL <40/<50; TG ≥150 (604) | Đúng theo ADA rec 10.15 và QĐ 5481 Bảng 4 | | Giữ |
| cạnh hút thuốc → ĐTĐ típ 2 (nguồn who-smoking…) | Nguồn không chứa | | Đổi nguồn |

---

## 7. Điểm Việt Nam khác ADA 2026

| Chủ đề | ADA 2026 | QĐ 5481 (VN) | Khuyến nghị cho chatbot |
|---|---|---|---|
| Tuổi bắt đầu sàng lọc | 35 | 45 | Nêu cả hai |
| Lặp lại sàng lọc khi bình thường | ≥ mỗi 3 năm | 1–3 năm | Nêu "1–3 năm tùy nguy cơ" |
| Huyết áp là yếu tố nguy cơ | ≥130/80 | ≥140/90 | Nêu cả hai |
| Tiền ĐTĐ (định nghĩa) | Có | Không có trong văn bản đã đọc | Dùng ADA, ghi rõ |
| Chẩn đoán tăng huyết áp | ≥130/80 (2 lần đo, 2 dịp) | ≥140/90 sau đo lại; 130–139/80–89 điều chỉnh lối sống tối đa 3 tháng | Nêu cả hai |
| Mục tiêu huyết áp | <130/80; SBP<120 nếu nguy cơ cao | <140/90; <130/80 nếu thận/nguy cơ cao | Nêu cả hai |
| LDL | <70 (nguy cơ cao), <55 (đã có ASCVD) | <100, <70, <50 | Nêu cả hai |
| HbA1c người lớn tuổi | <8% (phức tạp) | <7,5 / <8,0 / <8,5% | Nêu cả hai |
| Rượu bia | ≤1 nữ, ≤2 nam; theo oz | 1–2 đơn vị (10 g cồn) | Dùng ml theo VN |
| Vận động | ≥150 phút, ≥3 ngày | 150 phút, tập 5 ngày/tuần | Nêu cả hai |
| Giảm cân | ≥5–7% | 5–10% trong 3–6 tháng | Nêu cả hai |
| OGTT chuẩn bị | ≥150 g carbohydrate/ngày | 150–200 g | Nêu "≥150 g" |
| Khám mắt sau lần đầu bình thường | Hằng năm; có thể 1–2 năm | Mỗi 1–2 năm | Nêu cả hai |
| Khám chân | Hằng năm; phân tầng 1–12 tháng | Hằng năm + mỗi lần khám | Nêu "ít nhất hằng năm" |
| Hạ đường huyết xử trí | 15 g | 15–20 g, glucagon từ mức 2 | Giữ 15–20 g |
| ĐTĐ thai kỳ | một bước hoặc hai bước | một bước (92/180/153) | App dùng một bước, đúng |
| Vòng eo | — | <90 nam, <80 nữ | Giữ |
| Thang HbA1c theo dõi | — | mỗi 3 tháng; ít nhất 2 lần/năm nếu ổn định | Thêm nếu cần |

---

## 8. Việc chưa làm được / nguồn vẫn không đọc được

- Toàn văn ADA bản "Abridged for Primary Care" (Europe PMC HTTP 500).
- Các mục ADA S2/S5/S6/S10/S11/S12/S15 mới đọc phần đầu (khuyến nghị và bảng); chưa đọc hết thân bài.
- QĐ 1353 bản gốc (chỉ có tóm tắt từ caselaw.vn).
- WHO IRIS 10665/206936 (403), IDF (lỗi chuyển hướng), Long Châu (403), bảng số của Alberti 2009, DPP (NEJM 2002), KDIGO, WHO 2020 guideline on physical activity.
- Trang Vinmec `dau-hieu-som-cua-tieu-duong-type-2-vi`.
- `knowledge/eval_questions.json` và `web_sources.json`: chưa rà; nếu có câu hỏi dựa trên số 35 tuổi/130/80/14 g cồn thì cần cập nhật đáp án theo mục 7.
