# Nguồn dữ liệu và định nghĩa bài toán

## BRFSS 2021–2023

Tải **SAS Transport** (không phải ASCII) và tài liệu/codebook từ [2021](https://www.cdc.gov/brfss/annual_data/annual_2021.html), [2022](https://www.cdc.gov/brfss/annual_data/annual_2022.html), [2023](https://www.cdc.gov/brfss/annual_data/annual_2023.html); giải nén và đặt các tệp vào `data/raw/` với tên `LLCP2021.XPT`, `LLCP2022.XPT`, `LLCP2023.XPT` hoặc dùng đường dẫn thực tế khi chạy lệnh huấn luyện.

Pipeline chọn `_AGEG5YR`, `_BMI5` (chia 100), `SEXVAR`, `_SMOKER3`, `_TOTINDA`; nhãn `DIABETE4`: 1 = từng được báo mắc tiểu đường, 3 = không; loại 2 (thai kỳ), 4 (tiền tiểu đường), thiếu/không rõ. Loại các mã không biết/từ chối khỏi đặc trưng, sau đó impute dựa trên tập train. `_AGEG5YR` 1 là 18–24 tuổi, 2 là 25–29 tuổi, sau đó tăng mỗi 5 năm đến 13 là 80+. **Phải đối chiếu codebook của tất cả các phiên bản tải về trước khi dùng**; mã dừng nếu thiếu cột. Các phép phân chia: 2021–22 train/validation (80/20 phân tầng), 2023 là test theo thời gian. Không bảo đảm một người không tham gia ở nhiều năm; cần nêu điều này khi báo cáo. Không dùng trọng số khảo sát; số liệu không đại diện cho ước lượng dân số.

Dữ liệu và artifact được `.gitignore` loại trừ. Kiểm tra điều kiện sử dụng nguồn trước khi phân phối.

## UCI Early Stage

Tải CSV từ [UCI Early Stage Diabetes Risk Prediction](https://archive.ics.uci.edu/dataset/529/early%2Bstage%2Bdiabetes%2Brisk%2B), đặt tên `data/raw/diabetes_data_upload.csv`. Pipeline giữ 16 biến đầu vào và nhãn `class`, loại hồ sơ trùng trước khi chia tập (và loại hồ sơ có nhãn xung đột), chia train/validation/test phân tầng, không gộp với BRFSS. Bản CSV đã tải có 520 dòng nhưng chỉ có 251 hồ sơ duy nhất (269 dòng trùng); dữ liệu sau loại trùng rất nhỏ và lấy từ một bệnh viện; không suy rộng kết quả cho lâm sàng hoặc dân số Việt Nam.

## Tri thức

`knowledge/sources.json` là tập đoạn giới thiệu ngắn, không phải knowledge base y tế hoàn chỉnh. Hãy kiểm tra tính chính xác, cập nhật, giấy phép, phân đoạn, metadata và chất lượng truy xuất trước khi mở rộng; không sao chép nguyên văn hàng loạt tài liệu có bản quyền. Chỉ dùng nguồn đã được kiểm chứng và trích URL.

Biến `_RFHYPE6` không có trong bộ 2022 đã tải, nên không dùng làm đầu vào cho bộ ba năm.

## Đối chiếu assignment cũ (04/11/2026)

- `intel-sys-assignment-03/data/diabets_new.csv` và `intel-sys-assignment-04/dataset/diabets.csv`: 324.372 dòng, 21 biến và nhãn `Diabetes_binary`; assignment 04 gọi đây là BRFSS. Chưa xác minh được năm khảo sát, nguồn tải gốc, cách tạo nhãn hoặc giấy phép của bản đã xử lý. Cần đối chiếu dữ liệu gốc và codebook trước khi huấn luyện; không gộp hoặc dùng làm test độc lập với BRFSS hiện tại khi chưa loại trừ trùng người/bản ghi.
- `intel-sys-assignment-02/data/diabetes.csv`: 403 dòng; có `glyhb`, glucose và các chỉ số khác, nhưng không có nhãn bệnh độc lập trong bản CSV.
- `intel-sys-assignment-07/data/diabetes.csv` và assignment 08: 403 dòng, cột `Outcome` được tạo từ `glyhb > 6.5` theo `intel-sys-assignment-07/fix_datasets.py`. Nếu dùng `glyhb` dự đoán `Outcome`, mô hình chỉ học lại quy tắc tạo nhãn; không đánh giá được khả năng dự đoán bệnh độc lập. Chưa dùng tập này thay thế mô hình hiện tại.

Bộ hiện dùng vẫn là UCI Early Stage và BRFSS 2021–2023. Cần xác định mục tiêu nhãn và đối tượng triển khai trước khi đổi dataset; hiện không có bằng chứng các bộ assignment phù hợp hơn cho người dùng Việt Nam.
