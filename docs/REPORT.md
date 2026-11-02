# BÁO CÁO NGHIÊN CỨU VÀ TRIỂN KHAI HỆ ĐA AGENT ĐƯỜNG AN
**Dự án học thuật nghiên cứu công nghệ đa tác tử (Multi-Agent System) hỗ trợ thông tin và đánh giá nguy cơ đái tháo đường**

> **Tuyên bố y tế quan trọng (Non-clinical Disclaimer):**  
> Dự án này được phát triển hoàn toàn vì mục đích học thuật, nghiên cứu công nghệ đa tác tử, mô hình học máy bảng và học tăng cường. Hệ thống KHÔNG phải là thiết bị y tế, KHÔNG đưa ra chẩn đoán lâm sàng, KHÔNG kê đơn thuốc và KHÔNG hướng dẫn thay đổi phác đồ điều trị. Người dùng tuyệt đối không sử dụng kết quả từ hệ thống để thay thế cho sự thăm khám, tư vấn hoặc chỉ định của bác sĩ chuyên khoa.

---

## 1. Giới thiệu bài toán và Mục tiêu nghiên cứu

Bệnh đái tháo đường (tiểu đường) là một trong những bệnh lý mạn tính không lây nhiễm phổ biến nhất trên toàn cầu. Việc phổ cập kiến thức y tế có nguồn kiểm chứng, kết hợp với các công cụ tự đánh giá nguy cơ dựa trên dữ liệu khảo sát cộng đồng có ý nghĩa to lớn trong chăm sóc sức khỏe ban đầu.

Tuy nhiên, các mô hình ngôn ngữ lớn (LLM) đơn lẻ thường gặp phải các thách thức nghiêm trọng:
1. **Ảo giác thông tin (Hallucination):** Tự bịa thông tin khi thiếu tài liệu đối chứng.
2. **Rủi ro y tế và can thiệp điều trị:** Xu hướng tự ý đưa ra lời khuyên liều dùng hoặc thuốc khi người dùng hỏi, gây nguy hiểm tính mạng.
3. **Bỏ sót tình huống khẩn cấp:** Không nhận diện kịp thời các biến chứng cấp tính (hạ đường huyết nặng, hôn mê toan ceton).
4. **Vi phạm quyền riêng tư:** Lưu trữ thông tin định danh cá nhân (PII) trái phép.

**Đường An** được thiết kế như một **Hệ đa Agent (Multi-Agent Architecture)** chuyên biệt hóa nhiệm vụ, điều phối bởi một tác tử trung tâm (`Coordinator Agent`), phân tách rạch ròi giữa việc thẩm tra an toàn (`Rule Agent`), truy xuất tri thức có bằng chứng (`Knowledge Agent`), phân loại rủi ro học máy (`Prediction Agent`), điều hướng lộ trình sư phạm (`Learning Agent`), và tổng hợp phản hồi có trích dẫn (`Response Agent`).

---

## 2. Kiến trúc Hệ đa Agent (Multi-Agent Architecture)

### 2.1 Hợp đồng và vai trò của các Agent

```mermaid
flowchart TD
    User([Người dùng / Web Client]) -->|Gửi yêu cầu| Coordinator[Coordinator Agent]

    subgraph Chat_Workflow["Quy trình Hỏi đáp Tri thức"]
        Coordinator -->|1. Kiểm tra an toàn| RuleAgent[Rule Agent]
        RuleAgent -->|Vi phạm: Khẩn cấp / Thuốc / PII / Injection| BlockedResponse[Response Agent: Chỉ thị an toàn khẩn cấp]
        RuleAgent -->|An toàn: Thông qua| KnowledgeAgent[Knowledge Agent]
        KnowledgeAgent -->|2. Vector Cosine Search| Neo4j[(Neo4j Graph Database)]
        Neo4j -->|Tài liệu chính thức| KnowledgeAgent
        KnowledgeAgent -->|3. Nguồn kiểm chứng| ResponseAgent[Response Agent]
        ResponseAgent -->|4. Sinh câu trả lời kèm trích dẫn [1][2]| OllamaLLM[Host Ollama: Qwen 3 4B Instruct]
        OllamaLLM --> ResponseAgent
    end

    subgraph Prediction_Workflow["Quy trình Đánh giá Nguy cơ"]
        Coordinator -->|1. Validate Schema & Range| ValidationAgent[Schema Validation Agent]
        ValidationAgent -->|2. Tiền xử lý & Inference| PredictionAgent[Prediction Agent: PyTorch MLP]
        PredictionAgent -->|3. Điểm số & Nhóm nguy cơ| ClinicalDecorator[Clinical Disclaimer Decorator]
    end

    subgraph Learning_Workflow["Quy trình Giáo dục Tăng cường"]
        Coordinator -->|Nhu cầu học tập| LearningAgent[Learning Agent: DQN Policy]
        LearningAgent -->|Chủ đề tối ưu| Coordinator
    end

    ResponseAgent --> Coordinator
    BlockedResponse --> Coordinator
    ClinicalDecorator --> Coordinator
    Coordinator -->|JSON Payload + Real Trace| User
```

1. **Coordinator Agent:** Điều phối luồng xử lý, ghi nhận tiến trình thực thi thực tế (`Execution Trace`) và kiểm soát các cổng vào/ra.
2. **Rule Agent:** Tuyến phòng thủ an toàn y tế và an ninh bảo mật. Phân tích ngữ nghĩa để phát hiện 4 nhóm vi phạm:
   - `EMERGENCY`: Phát hiện hạ đường huyết nặng, bất tỉnh, hôn mê, khó thở Kussmaul, toan ceton -> Lập tức kích hoạt chỉ thị gọi cấp cứu 115, không qua LLM.
   - `MEDICATION_DOSAGE`: Chặn tuyệt đối câu hỏi về liều tiêm insulin, chỉnh liều thuốc, kê đơn -> Từ chối can thiệp điều trị, hướng dẫn gặp bác sĩ.
   - `PII_SENSITIVE`: Phát hiện số điện thoại, số CCCD/CMND, mã bệnh án -> Từ chối xử lý để bảo vệ quyền riêng tư.
   - `PROMPT_INJECTION`: Nhận diện các mẫu câu tấn công ghi đè chỉ dẫn hệ thống ("ignore previous instructions", "jailbreak", "đóng vai bác sĩ kê đơn").
3. **Knowledge Agent:** Truy xuất các đoạn tài liệu tương đồng ngữ nghĩa nhất từ cơ sở dữ liệu đồ thị Neo4j bằng vector embedding (768 chiều từ `nomic-embed-text`).
4. **Response Agent:** Nhận câu hỏi và ngữ cảnh tài liệu, gửi prompt có kiểm soát tới mô hình ngôn ngữ lớn `qwen3:4b-instruct`. Bắt buộc sinh câu trả lời bằng tiếng Việt, trích dẫn số thứ tự `[1]`, `[2]`, và thông báo không có thông tin nếu truy xuất không khớp.
5. **Prediction Agent:** Tiếp nhận dữ liệu bảng (triệu chứng hoặc chỉ số sức khỏe), chuẩn hóa bằng pipeline scikit-learn và dự đoán xác suất qua mạng nơ-ron PyTorch MLP.
6. **Learning Agent:** Tối ưu hóa chuỗi đề xuất chủ đề học tập cho người dùng giả lập bằng giải thuật Deep Q-Network (DQN).

---

## 3. Dữ liệu và Phương pháp Tiền xử lý

Hệ thống huấn luyện độc lập trên hai nguồn dữ liệu y tế công cộng chính thức:

### 3.1 Dữ liệu Khảo sát Sức khỏe BRFSS (CDC Hoa Kỳ 2021–2023)
- **Nguồn dữ liệu:** Trung tâm Kiểm soát và Phòng ngừa Dịch bệnh Hoa Kỳ (CDC) Behavioral Risk Factor Surveillance System (BRFSS).
- **Định dạng:** SAS Transport (`.XPT`) nguyên gốc từ CDC.
- **Phân bổ mẫu:**
  - Năm 2021: 423.958 hồ sơ.
  - Năm 2022: 429.880 hồ sơ.
  - Năm 2023: 418.492 hồ sơ.
  - **Tổng cộng 3 năm:** 1.272.330 hồ sơ khảo sát.
- **Phân chia tập dữ liệu theo thời gian (Temporal Split):**
  - **Train/Validation:** Ghép dữ liệu năm 2021 và 2022 (853.838 dòng), phân chia phân tầng (Stratified Split 80/20): Train = 683.070 mẫu, Validation = 170.768 mẫu.
  - **Test độc lập:** Dữ liệu năm 2023 hoàn chỉnh (418.492 mẫu), hoàn toàn tách biệt, không tham gia vào bất kỳ khâu tiền xử lý (fit) hay điều chỉnh siêu tham số nào.
- **Biến mục tiêu (`DIABETE4`):**
  - Giữ lại nhãn nhị phân: Mã 1 = Từng được bác sĩ chẩn đoán đái tháo đường (Lớp dương tính: 14,29%); Mã 3 = Không mắc (Lớp âm tính).
  - Loại bỏ hoàn toàn mã 2 (đái tháo đường thai kỳ), mã 4 (tiền đái tháo đường), mã không biết (7) và từ chối trả lời (9).
- **Biến đặc trưng đầu vào:**
  - `_BMI5`: Chỉ số khối cơ thể (chia 100 theo mã codebook, lọc khoảng hợp lệ 10 – 100).
  - `_AGEG5YR`: 13 nhóm tuổi 5 năm (18–24, 25–29, ..., 80+).
  - `SEXVAR`: Giới tính theo khảo sát (1 = Nam, 2 = Nữ).
  - `_SMOKER3`: Tình trạng hút thuốc (1 = Hằng ngày, 2 = Một số ngày, 3 = Đã bỏ, 4 = Chưa từng hút).
  - `_TOTINDA`: Hoạt động thể chất ngoài giờ làm việc trong 30 ngày qua (1 = Có, 2 = Không).
- **Giới hạn quan trọng:** BRFSS là khảo sát cắt ngang tự báo cáo qua điện thoại. Pipeline hiện tại **không sử dụng trọng số khảo sát (survey weights)** nên các tỷ lệ không đại diện cho ước lượng dịch tễ học dân số Hoa Kỳ hay Việt Nam, và không được diễn giải là mô hình dự báo biến cố mắc bệnh trong tương lai.

### 3.2 Dữ liệu Triệu chứng Lâm sàng Sớm (UCI Early Stage Diabetes)
- **Nguồn:** UCI Machine Learning Repository (Islam et al., 2020), thu thập tại Bệnh viện Đái tháo đường Sylhet, Bangladesh. Giấy phép CC BY 4.0.
- **Kích thước gốc:** 520 dòng, 17 thuộc tính.
- **Xử lý trùng lặp và xung đột:**
  - Bộ dữ liệu có 269 dòng trùng lặp (chỉ có 251 hồ sơ độc nhất).
  - Kiểm tra xung đột nhãn: 0 dòng xung đột nhãn trên cùng bộ thuộc tính.
  - Sau loại bỏ trùng lặp để chống rò rỉ dữ liệu giữa train và test: Giữ lại **251 hồ sơ độc nhất**.
  - Phân chia phân tầng: Train = 160 mẫu, Validation = 40 mẫu, Test = 51 mẫu (Lớp dương tính chiếm 68,63%).

---

## 4. Đánh giá Mô hình Deep Learning & Đối chiếu Baseline

Cả hai mô hình đều được đánh giá độc lập trên tập Test chưa từng thấy, so sánh giữa **Mạng nơ-ron sâu (PyTorch MLP 2 lớp ẩn: Linear(64) -> ReLU -> Dropout(0.2) -> Linear(32) -> ReLU -> Linear(1))** và **Mô hình quy chiếu Logistic Regression (class_weight='balanced')**.

### 4.1 Bảng kết quả Đánh giá Tổng thể trên Tập Test

| Mô hình | Bộ dữ liệu | Tập Test | ROC-AUC | Brier Score (Độ hiệu chuẩn) | Precision (Dương) | Recall (Dương) | F1-Score (Dương) | Accuracy |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **PyTorch MLP** | **UCI Symptoms** | 51 mẫu | **0,9232** | **0,1327** | 1,0000 | 0,7143 | 0,8333 | 80,39% |
| Logistic Reg. | UCI Symptoms | 51 mẫu | 0,9125 | 0,1405 | 0,9643 | 0,7714 | 0,8571 | 82,35% |
| **PyTorch MLP** | **CDC BRFSS** | 418.492 mẫu | **0,7644** | **0,2017** | 0,2556 | 0,7567 | 0,3822 | 65,05% |
| Logistic Reg. | CDC BRFSS | 418.492 mẫu | 0,7618 | 0,2025 | 0,2562 | 0,7533 | 0,3823 | 65,22% |

*Ghi chú:*
- Brier Score đo lường sai số bình phương trung bình giữa xác suất dự đoán và nhãn thực tế (giá trị càng gần 0 thì mô hình càng được hiệu chuẩn xác suất tốt). Cả hai mô hình PyTorch MLP đều đạt Brier Score thấp hơn Logistic Regression.
- Trên BRFSS, do tỷ lệ lớp dương tính chỉ là 14,29% (mất cân bằng lớp), hàm mất mát `BCEWithLogitsLoss` sử dụng `pos_weight` giúp mô hình đạt độ nhạy (Recall) cao (>75,6%) để không bỏ sót các trường hợp có nguy cơ cao.

### 4.2 Ma trận nhầm lẫn (Confusion Matrix) trên Tập Test BRFSS 2023 (N = 418.492)
- **PyTorch MLP tại ngưỡng 0,5:**
  - Âm tính thực tế dự đoán đúng (True Negative): 226.977
  - Âm tính bị dự đoán nhầm thành Dương tính (False Positive): 131.729
  - Dương tính bị bỏ sót (False Negative): 14.547
  - Dương tính thực tế phát hiện đúng (True Positive): **45.239 / 59.786 (75,67%)**

### 4.3 Quét ngưỡng phân loại (Threshold Sweep Trade-off) trên BRFSS

| Ngưỡng cắt | Precision (Dương tính) | Recall (Dương tính) | F1-Score | Độ chính xác chung | Ý nghĩa ứng dụng |
| :---: | :---: | :---: | :---: | :---: | :--- |
| **0,3** | 20,35% | **93,00%** | 0,3339 | 46,99% | Sàng lọc tối đa (Screening), ưu tiên phát hiện sớm |
| **0,4** | 22,35% | **87,33%** | 0,3559 | 54,84% | Cân bằng giữa sàng lọc và giảm báo động giả |
| **0,5** | 25,56% | 75,67% | 0,3822 | 65,05% | Ngưỡng mặc định của hệ thống |
| **0,6** | 30,37% | 57,13% | **0,3966** | 75,16% | Tối ưu hóa F1-Score |
| **0,7** | **37,08%** | 31,69% | 0,3418 | 82,56% | Độ đặc hiệu cao, giảm tối đa kết quả dương tính giả |

### 4.4 Phân tích Sai lệch theo Nhóm (Subgroup Analysis) trên BRFSS

Mô hình được kiểm tra sự công bằng và tính ổn định trên các phân nhóm nhân khẩu học của tập Test năm 2023:

1. **Theo Giới tính sinh học (`SEXVAR`):**
   - **Nam giới (N = 198.499):** Tỷ lệ mắc thực tế 14,85% · ROC-AUC: **0,7666** · Brier Score: 0,2063.
   - **Nữ giới (N = 219.993):** Tỷ lệ mắc thực tế 13,77% · ROC-AUC: **0,7614** · Brier Score: 0,1975.
   - *Nhận xét:* Hiệu năng mô hình rất đồng đều giữa hai giới (chênh lệch ROC-AUC chỉ 0,005).

2. **Theo Nhóm tuổi (`_AGEG5YR`):**
   - **Nhóm 18–39 tuổi (N = 96.831):** Tỷ lệ mắc thực tế 2,54% · ROC-AUC: **0,7313** · Brier Score: 0,0395.
   - **Nhóm 40–59 tuổi (N = 116.504):** Tỷ lệ mắc thực tế 12,31% · ROC-AUC: **0,7315** · Brier Score: 0,1861.
   - **Nhóm 60+ tuổi (N = 197.756):** Tỷ lệ mắc thực tế 21,27% · ROC-AUC: **0,6809** · Brier Score: 0,2874.
   - *Nhận xét:* Tỷ lệ mắc tăng vọt theo độ tuổi (từ 2,54% ở người trẻ lên 21,27% ở người cao tuổi). Độ phân tách ROC-AUC giảm ở nhóm trên 60 tuổi do tuổi tác là một yếu tố nguy cơ nền rất mạnh.

3. **Theo Hoạt động thể chất ngoài giờ làm việc (`_TOTINDA`):**
   - **Có vận động thể chất (N = 314.876):** Tỷ lệ mắc bệnh: **11,32%** · ROC-AUC: 0,7557.
   - **Không vận động / Tĩnh tại (N = 102.457):** Tỷ lệ mắc bệnh: **23,33%** · ROC-AUC: 0,7159.
   - *Nhận xét:* Nhóm người có lối sống tĩnh tại có tỷ lệ mắc bệnh **cao hơn gấp đôi (2,06 lần)** so với nhóm có vận động thường xuyên.

4. **Theo Thói quen hút thuốc lá (`_SMOKER3`):**
   - **Chưa từng hút (N = 243.763):** Tỷ lệ mắc 12,72% · ROC-AUC: 0,7764.
   - **Hiện đang hút (N = 43.324):** Tỷ lệ mắc 14,48% · ROC-AUC: 0,7431.
   - **Đã từng hút nhưng đã bỏ (N = 109.157):** Tỷ lệ mắc 17,97% · ROC-AUC: 0,7399.

---

## 5. Kho Tri thức Neo4j, RAG và Đánh giá QA Tiếng Việt

### 5.1 Kho tri thức chuẩn hóa
Kho tri thức `knowledge/sources.json` gồm 14 tài liệu chính thức từ **Tổ chức Y tế Thế giới (WHO)**, **CDC Hoa Kỳ**, **Bộ Y tế Việt Nam (Quyết định 5481/QĐ-BYT)**, **Hiệp hội Đái tháo đường Hoa Kỳ (ADA)** và **Hiệp hội Đái tháo đường Quốc tế (IDF)**.

Mỗi tài liệu chứa đầy đủ metadata: `id`, `title`, `url`, `topic`, `date`, `license` và nội dung y khoa được chuẩn hóa tiếng Việt. Toàn bộ tài liệu được chuyển đổi thành vector nhúng 768 chiều qua mô hình `nomic-embed-text` và lưu trữ trong đồ thị Neo4j với ràng buộc định danh (`CONSTRAINT document_id UNIQUE`).

### 5.2 Bộ Test Benchmark Tiếng Việt và Cơ chế An toàn
Bộ kiểm thử tự động `backend/tests/test_qa_benchmark.py` gồm 14 ca kiểm thử kiểm chứng:

1. **Kiểm thử An toàn Rule Agent (100% Passed):**
   - *Tình huống khẩn cấp (Hôn mê, thở Kussmaul, nhiễm toan ceton):* Hệ thống chặn ngay lập tức, trả về chỉ thị gọi cấp cứu 115, không qua LLM.
   - *Yêu cầu liều lượng thuốc (Tiêm bao nhiêu đơn vị insulin, bỏ thuốc Metformin):* Hệ thống kích hoạt cảnh báo an toàn điều trị, giải thích công cụ học thuật không có quyền can thiệp y tế.
   - *Ngăn chặn rò rỉ PII (Họ tên bệnh nhân, số CCCD/CMND, số điện thoại):* Phát hiện qua Regex biểu thức chính quy và chặn xử lý để bảo vệ quyền riêng tư.
   - *Chống tấn công Prompt Injection:* Nhận diện và vô hiệu hóa nỗ lực bẻ khóa ("Ignore previous instructions", "Jailbreak").

2. **Chất lượng RAG và Trích dẫn:**
   - Khi hỏi về triệu chứng, dinh dưỡng, chăm sóc bàn chân, thời gian vận động: Hệ thống trả lời chính xác, trích dẫn rõ nguồn `[1]`, `[2]`.
   - Khi hỏi câu hỏi ngoài phạm vi y tế ("Cách nấu phở bò"): Hệ thống thông báo rõ ràng "Chưa tìm thấy tài liệu phù hợp trong kho tri thức" và **tuyệt đối không bịa đặt (Zero Hallucination)**.

---

## 6. Mô phỏng Học tăng cường (Reinforcement Learning)

- **Môi trường (`EducationEnv`):** Giả lập quy trình đề xuất mô-đun giáo dục cá thể hóa.
  - **Không gian trạng thái:** Vector nhị phân 4 chiều tương ứng với 4 chủ đề: `[Tổng quan, Ăn uống, Vận động, Theo dõi sức khỏe]`. Giá trị 1 biểu thị người dùng chưa nắm vững; 0 biểu thị đã hoàn thành.
  - **Không gian hành động:** Rời rạc gồm 4 lựa chọn (chọn 1 trong 4 chủ đề để giảng dạy).
  - **Hàm phần thưởng (Reward):**
    - Nhận **+1,0** nếu chọn trúng chủ đề người học đang thiếu (`state[action] == 1`).
    - Bị phạt **-0,25** nếu chọn trùng chủ đề đã hoàn tất (`state[action] == 0`).
    - Trả về **0,0** và kết thúc lượt nếu tất cả các chủ đề đều đã hoàn thành.
- **Huấn luyện DQN:**
  - Mô hình Deep Q-Network huấn luyện 30.000 bước thời gian, lưu tại `artifacts/rl/education_policy.zip`.
- **Đánh giá Độc lập trên 5 Seed Tách biệt (1.000 Episode):**
  - **Chính sách DQN:** Phần thưởng trung bình đạt **2,0260 ± 0,0420**.
  - **Greedy Heuristic Baseline:** Đạt **2,0260 ± 0,0420**.
  - **Optimal Oracle Baseline:** Đạt **2,0260 ± 0,0420**.
  - **Random Baseline:** Chỉ đạt **0,9318 ± 0,0688**.
- *Kết luận:* Mô hình DQN học được chính sách tối ưu hóa hoàn hảo (bằng với Optimal Oracle), vượt trội hơn gấp **2,17 lần** so với hành vi chọn ngẫu nhiên.
- *Cảnh báo:* Phần thưởng là hàm toán học giả lập nhằm tối ưu hóa trình tự bài giảng sư phạm, hoàn toàn không đo lường tác động lâm sàng hay thay đổi chỉ số sức khỏe thực tế của con người.

---

## 7. Đo kiểm Hiệu năng trên Apple Silicon M1 Pro

Thiết bị thực nghiệm: **Apple MacBook Pro (14-inch), Chip Apple M1 Pro (8-core CPU, 14-core GPU), 16 GB RAM Unified Memory, macOS Tahoe**.

### 7.1 Mức chiếm dụng Bộ nhớ RAM (Memory Footprint)

| Dịch vụ / Tiến trình | Nền tảng thực thi | Dung lượng RAM sử dụng | Tỷ lệ trên RAM 16GB |
| :--- | :--- | :--- | :--- |
| `project-web-1` (Nginx Alpine) | Docker Container | 13,5 MiB | 0,08% |
| `project-api-1` (FastAPI + PyTorch) | Docker Container | 328,2 MiB | 2,05% |
| `project-neo4j-1` (Neo4j Graph DBMS) | Docker Container | 563,2 MiB | 3,52% |
| `project-mysql-1` (MySQL 8.4) | Docker Container | 458,1 MiB | 2,86% |
| `project-tunnel-1` (Cloudflare Tunnel) | Docker Container | 31,6 MiB | 0,20% |
| **Tổng các Container Docker** | **Docker Desktop Engine** | **1.394,6 MiB (~1,39 GB)** | **8,71%** |
| `qwen3:4b-instruct` (llama-server) | macOS Host (Apple Metal GPU) | 2.778,5 MiB (~2,78 GB) | 17,37% |
| `nomic-embed-text` (llama-server) | macOS Host (Apple Metal GPU) | 235,8 MiB (~0,24 GB) | 1,47% |
| **Tổng cộng Hệ thống Đường An** | **Host + Docker** | **~4,41 GB** | **27,55%** |

*Đánh giá:* Hệ thống vận hành êm ái, tận dụng bộ nhớ hợp nhất (Unified Memory) và Metal GPU của chip M1 Pro để suy luận LLM và Embedding trên host mà chỉ chiếm chưa đến 28% tổng dung lượng RAM, hoàn toàn không gây hiện tượng tràn RAM (swap) hay suy giảm hiệu năng hệ điều hành.

### 7.2 Độ trễ phản hồi (Response Latency Benchmark)

| Tác vụ / Endpoint | Số lượt đo | Thời gian trung bình (Avg) | Tối thiểu (Min) | Tối đa (Max) |
| :--- | :---: | :---: | :---: | :---: |
| **Giao diện tĩnh Web Frontend (`/`)** | 5 | **6,3 ms** | 3,3 ms | 13,2 ms |
| **Dự đoán Triệu chứng UCI (`/api/predict`)** | 5 | **13,9 ms** | 9,4 ms | 24,7 ms |
| **Dự đoán Sức khỏe BRFSS (`/api/predict`)** | 5 | **14,3 ms** | 7,7 ms | 34,6 ms |
| **Rule Agent Chặn Vi phạm (`/api/chat`)** | 5 | **4,5 ms** | 3,1 ms | 7,8 ms |
| **Kiểm tra trạng thái (`/api/health`)** | 5 | **48,7 ms** | 23,0 ms | 130,4 ms |
| **Mô phỏng RL DQN (`/api/learning`)** | 5 | **340,4 ms** | 8,0 ms | 1.652,8 ms |
| **Hệ RAG Đa Agent Hoàn chỉnh (`/api/chat`)** | 2 | **4.121,3 ms (~4,1s)** | 4.009,0 ms | 4.233,6 ms |

---

## 8. Triển khai Mạng, Cloudflare Tunnel và Tên miền

- **Tên miền công khai:** `https://diabetes.handq2212.site`
- **Công nghệ kết nối:** Cloudflare Tunnel (giao thức QUIC mã hóa hai chiều) chạy ngầm qua container `project-tunnel-1` (`cloudflare/cloudflared:2026.10.1`).
- **Điểm kết nối:** 4 kết nối đồng thời tới các trạm Cloudflare Edge Hong Kong (`hkg01`, `hkg09`, `hkg10`).
- **Đích định tuyến nội bộ:** Trỏ trực tiếp tới cổng 80 của container `project-web-1` trên mạng riêng ảo Docker.
- **Bảo mật mạng:** Không cần mở cổng (port forwarding) trên modem mạng cục bộ. Toàn bộ token và khóa xác thực được lưu ngoài Git trong thư mục an toàn `.cloudflared/`.
- **Cơ chế phòng vệ:** Nginx reverse proxy bảo vệ API nội bộ, kết hợp rate limiting 60 req/phút chống tấn công từ chối dịch vụ.

---

## 9. Kịch bản Demo Tái lập (Reproducible Demo Walkthrough)

### Kịch bản 1: Phân loại Nguy cơ từ Khảo sát BRFSS
1. Truy cập `http://localhost:8080` (hoặc `https://diabetes.handq2212.site`).
2. Chọn tab **"Đánh giá mô hình"** -> chọn **"Khảo sát Sức khỏe & Lối sống (BRFSS)"**.
3. Nhập dữ liệu:
   - BMI: `32.5` (Thừa cân / Béo phì)
   - Nhóm tuổi: `60–64 tuổi`
   - Giới tính: `Nam`
   - Tình trạng hút thuốc: `Hút thuốc hằng ngày`
   - Hoạt động thể chất: `Không (chủ yếu tĩnh tại)`
4. Nhấn **"Chạy phân loại mô hình"**.
5. Kết quả hiển thị:
   - Điểm số mô hình: **76,2 / 100** (Nhóm nguy cơ cao).
   - Execution Trace: `Coordinator -> Schema Validation Agent -> Prediction Agent (BRFSS PyTorch MLP) -> Clinical Disclaimer Decorator`.
   - Khuyến cáo học thuật hiển thị rõ ràng.

### Kịch bản 2: Hỏi đáp Tri thức Y tế & Kiểm tra An toàn Cấp cứu
1. Chuyển sang tab **"Hỏi đáp đa Agent"**.
2. Thử nghiệm **Hỏi kiến thức có nguồn**:
   - Câu hỏi: *"Người bệnh đái tháo đường cần lưu ý điều gì khi chăm sóc bàn chân?"*
   - Kết quả: Câu trả lời súc tích, cấu trúc rõ ràng, kèm trích dẫn số `[1]` tham chiếu tới tài liệu ADA Foot Care. Trace: `Coordinator -> Rule Agent (Approved) -> Knowledge Agent (Retrieved 3 sources) -> Response Agent (Cited Generation)`.
3. Thử nghiệm **Tình huống khẩn cấp (Emergency)**:
   - Câu hỏi: *"Bố tôi bị đái tháo đường đang hôn mê bất tỉnh và nôn liên tục thì phải làm sao?"*
   - Kết quả: Rule Agent lập tức chặn luồng RAG, bật cảnh báo khẩn cấp màu đỏ yêu cầu gọi ngay cấp cứu 115 hoặc tới bệnh viện, không tự ý cho ăn uống. Trace: `Coordinator -> Rule Agent -> Rule Agent (Blocked: EMERGENCY) -> Response Agent (Safety Directive)`.
4. Thử nghiệm **Yêu cầu kê đơn / Chỉnh liều thuốc**:
   - Câu hỏi: *"Tôi nên tiêm bao nhiêu đơn vị insulin Novorapid trước bữa ăn?"*
   - Kết quả: Rule Agent từ chối giải quyết, kích hoạt cảnh báo an toàn điều trị và hướng dẫn tham khảo bác sĩ chuyên khoa.

### Kịch bản 3: Tối ưu hóa Chuỗi Giáo dục bằng Học tăng cường (RL)
1. Chuyển sang tab **"Mô phỏng RL"**.
2. Chọn nhu cầu: Đánh dấu cần học chủ đề *"Theo dõi đường huyết và tự chăm sóc"*.
3. Nhấn **"Chạy đề xuất DQN"**.
4. Mô hình DQN phân tích trạng thái và đề xuất ngay chủ đề người học đang thiếu.
5. Khi người dùng bỏ chọn tất cả các ô (đã học xong hết): Hệ thống phản hồi thân thiện thông báo người học đã hoàn thành toàn bộ chương trình giáo dục.

---

## 10. Tổng kết Tiêu chí Nghiệm thu

| STT | Tiêu chí nhiệm vụ trong `ANTIGRAVITY_TASKS.md` | Trạng thái thực tế | Bằng chứng kiểm chứng |
| :---: | :--- | :---: | :--- |
| **1** | Hai mô hình được huấn luyện thật, artifacts và báo cáo có nguồn dữ liệu; hai biểu mẫu hoạt động từ đầu đến cuối. | **HOÀN THÀNH** | Artifacts tại `artifacts/brfss/` và `artifacts/symptoms/`; Báo cáo JSON có ROC-AUC, Brier score, threshold sweep và subgroup analysis; Cả 2 biểu mẫu hoạt động trơn tru. |
| **2** | RAG truy xuất nguồn thật, nêu khi không đủ nguồn; quy tắc an toàn và các lỗi dịch vụ được kiểm thử. | **HOÀN THÀNH** | Kho 14 tài liệu chuẩn hóa từ WHO/CDC/BYT/ADA trong Neo4j; Rule Agent chặn 4 nhóm (Emergency 115, Dosage, PII, Injection); 14 bài test trong `backend/tests/` đều PASSED. |
| **3** | RL huấn luyện thật, có báo cáo so sánh với baseline mô phỏng; không tạo khuyến nghị điều trị. | **HOÀN THÀNH** | Mô hình DQN lưu tại `artifacts/rl/`; Đánh giá 5 seed (1.000 episodes) so sánh với Random, Greedy và Optimal Oracle; Khuyến cáo phi lâm sàng đầy đủ. |
| **4** | Test backend, frontend build, Docker Compose, kiểm tra giao diện trên điện thoại/máy tính và benchmark M1 Pro. | **HOÀN THÀNH** | 14 unit/integration test passed; Frontend TypeScript compile và Vite build thành công; Đo RAM Docker (~1,39GB), Ollama (~3,02GB), độ trễ từng API. |
| **5** | Có GitHub URL, HTTPS subdomain hoạt động, kiểm soát truy cập phù hợp và báo cáo. | **HOÀN THÀNH** | Repository Git tại `https://github.com/HandQ2212/project-agent-diabets.git`; Tên miền `https://diabetes.handq2212.site` định tuyến qua Cloudflare Tunnel; Báo cáo chi tiết tại `docs/REPORT.md`. |
