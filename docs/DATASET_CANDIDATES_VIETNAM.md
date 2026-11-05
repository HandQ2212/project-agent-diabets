# Khảo sát nguồn dữ liệu đái tháo đường cho người Việt Nam

Rà soát ngày 05/11/2026. Mục tiêu trước mắt là lựa chọn nguồn để nghiên cứu; chưa huấn luyện, chưa tải microdata và chưa xác nhận quyền sử dụng cho website. Số lượng biến không thay thế cho tính đúng đắn của nhãn, khả năng tái lập, thiết kế nghiên cứu hoặc kiểm định trên người Việt.

## Phân biệt bài toán

- **Phát hiện tình trạng hiện tại:** đầu vào và nhãn ở cùng lần khảo sát. Nếu nhãn được định nghĩa từ glucose, không đưa chính glucose hoặc biến suy ra từ nó vào đầu vào rồi coi kết quả cao là phát hiện độc lập. Chỉ số đo cùng lúc có thể được nghiên cứu trong một bài toán riêng được ghi rõ bản chất.
- **Dự đoán mắc mới trong tương lai:** cần người chưa mắc bệnh tại thời điểm gốc, các biến đo trước thời điểm dự đoán, kết quả theo dõi và thời gian theo dõi. Cần xử lý mất theo dõi/kiểm duyệt (censoring) và chọn trước thời hạn dự đoán. Hai khảo sát cắt ngang của các năm khác nhau không tự trở thành một cohort dọc.
- Trường hợp đã biết chẩn đoán, đang dùng thuốc hoặc có xét nghiệm là căn cứ tạo nhãn cần được xét riêng theo mục tiêu. Không gọi điểm số chưa hiệu chỉnh là xác suất bệnh hay sử dụng kết quả cho quyết định y tế.

## Các nguồn ưu tiên

| Nguồn | Dân số và dữ liệu | Nhãn, khả năng sử dụng | Đánh giá |
| --- | --- | --- | --- |
| [WHO/Bộ Y tế STEPS Việt Nam 2021](https://extranet.who.int/ncdsmicrodata/index.php/catalog/948) và [từ điển](https://extranet.who.int/ncdsmicrodata/index.php/catalog/948/data-dictionary/F1) | 4.435 bản ghi, 186 biến tổng; người lớn 18–69 tuổi, khảo sát toàn quốc. Có tuổi, giới, chiều cao, cân nặng, vòng eo/mông, huyết áp, glucose lúc đói, cholesterol toàn phần và HDL. Riêng `b5` glucose có 3.733 giá trị hợp lệ theo metadata, không phải số lượng ca đủ dữ liệu cho mô hình. | Cắt ngang. Có lịch sử tự khai về đường huyết và thuốc; cần kiểm tra codebook và mục tiêu cụ thể, không đồng nhất đường huyết cao tự khai với chẩn đoán xác định. Public-use nhưng điều kiện của WHO yêu cầu dùng phi thương mại vì sức khỏe cộng đồng, ghi nguồn, chia sẻ kế hoạch công bố với WHO và đề nghị đồng tác giả cho điều phối viên khảo sát. Trang truy cập microdata chưa được kiểm tra hoàn tất qua giao diện; chưa tải dữ liệu hay chấp nhận điều khoản thay người dùng. | Ưu tiên cho thí nghiệm Việt Nam về tình trạng tại thời điểm khảo sát, nếu đáp ứng điều kiện sử dụng. Không đủ để dự đoán mắc mới theo thời gian. |
| [STEPS Việt Nam 2015](https://extranet.who.int/ncdsmicrodata/index.php/catalog/590), [từ điển](https://extranet.who.int/ncdsmicrodata/index.php/catalog/590/data_dictionary) | 3.758 bản ghi, 163 biến tổng. Cũng là khảo sát Việt Nam cấp quốc gia. | Cắt ngang, không mặc định là cùng người với 2021. Cần đối chiếu biến, điều kiện truy cập, thay đổi đo lường và khả năng có cùng ca; chưa tải microdata. | Ứng viên đối chiếu giữa hai đợt, không coi là đánh giá ngoài độc lập cho đến khi kiểm tra quần thể và trùng lặp. |
| [Nghiên cứu Ninh Bình](https://pmc.ncbi.nlm.nih.gov/articles/PMC10297119/), [bản bài báo](https://pdfs.semanticscholar.org/0df1/08a609406f8df32bf956ca24bbfec230b0f6.pdf) | 2.153 người Việt nguy cơ cao, bài báo mô tả 14 cột gồm **13 thuộc tính và Outcome**: tuổi, giới, BMI, vòng eo, vòng mông, hai chỉ số huyết áp, glucose đói, glucose 2 giờ, cholesterol, triglyceride, HDL, insulin. | Tác giả cung cấp dữ liệu theo yêu cầu. Bài báo báo cáo dữ liệu thiếu nhiều ở một số xét nghiệm và còn 500 bản ghi sau tiền xử lý; chưa rõ điều kiện cấp phép hoặc dữ liệu nhãn độc lập với glucose. Chưa liên hệ tác giả. | Rất phù hợp về dân số và số thuộc tính, nhưng cần quyền truy cập, codebook, quy trình tạo nhãn và kiểm tra rò rỉ. Không đại diện toàn bộ dân số Việt Nam vì tuyển nhóm nguy cơ cao. |
| [Nghiên cứu cohort Việt Nam 5 năm](https://onlinelibrary.wiley.com/doi/abs/10.1111/dme.14680) | Nghiên cứu theo dõi người Việt trung niên với dữ liệu nhân trắc, lối sống và lâm sàng. | Mục tiêu mắc mới típ 2 trong 5 năm; dữ liệu theo yêu cầu tác giả. Chưa xác minh đủ số cột và điều kiện chia sẻ. | Ưu tiên nếu mục tiêu thực sự là dự báo tương lai; chưa có dữ liệu để huấn luyện. |
| [Rich Healthcare, Trung Quốc – Dryad](https://datadryad.org/dataset/doi:10.5061/dryad.ft8750v) | 211.833 người trưởng thành, 32 địa điểm, không mắc bệnh ban đầu, theo dõi trung vị 3,1 năm; file XLSX 28,34 MB được liệt kê. | Cohort hồi cứu với biến xét nghiệm và biến cố mắc mới. Nghiên cứu dùng glucose lúc đói và/hoặc tiền sử tự khai khi xác định biến cố trong thời gian theo dõi. Cần kiểm tra chính file, định nghĩa cột, điểm gốc, thời gian và điều khoản trước khi lập pipeline. | Ứng viên thực nghiệm theo dõi dọc lớn ở Đông Á; không phải dữ liệu Việt Nam, cần kiểm định trên cohort Việt độc lập. Chưa tải file. |
| [NAGALA, Nhật Bản – Dryad](https://datadryad.org/dataset/doi:10.5061/dryad.8q0p192) | 15.464 người, cohort hồi cứu tại Nhật, file XLSX 3,26 MB được liệt kê. Nghiên cứu gốc theo dõi trung vị hơn 5 năm. | Có kết cục mắc mới trong nghiên cứu; cần xem trực tiếp file, từ điển và điều khoản để xác định đúng cột cũng như số trường dùng được. | Có thể so sánh/kiểm định theo dữ liệu Đông Á với chú ý sai khác đối tượng và tiêu chí nhãn; không đại diện người Việt. Chưa tải file. |

## Các biến cần đánh giá

Với STEPS 2021, [từ điển dữ liệu](https://extranet.who.int/ncdsmicrodata/index.php/catalog/948/data-dictionary/F1) xác nhận các nhóm tuổi, giới, hành vi, huyết áp, chiều cao/cân nặng, vòng eo/vòng mông và một số xét nghiệm. Các biến như gia đình mắc bệnh, triglyceride, insulin, HbA1c không nên giả định có sẵn chỉ vì mong muốn biểu mẫu 15 trường; phải đối chiếu file và tỷ lệ thiếu.

Phác thảo hai bộ đầu vào để so sánh, không ép đủ 15:

1. **Không xét nghiệm:** tuổi, giới, chiều cao/cân nặng hoặc BMI, vòng eo, huyết áp, vận động, thuốc lá và các đặc trưng hợp lệ khác có tại thời điểm sử dụng. Phải kiểm tra những biến có thể đã thay đổi do biết bệnh.
2. **Có xét nghiệm:** chỉ bổ sung xét nghiệm đo trước thời điểm dự báo hoặc không nằm trong công thức tạo nhãn. Nếu glucose dùng để định nghĩa nhãn hiện tại thì phải loại khỏi đầu vào trong phân tích phát hiện độc lập. Giữ rõ thời điểm lấy mẫu và đơn vị.

Tên và số biến cuối cùng được quyết định sau khi xác minh codebook, số mẫu hợp lệ, tỷ lệ thiếu, số ca dương và mục tiêu. Không đưa ID, biến được đo sau kết cục, điều trị bệnh, hoặc các cột trực tiếp mã hóa nhãn vào mô hình.

## Quy trình tiếp theo

1. Chọn rõ một mục tiêu: phát hiện tình trạng tại thời điểm khảo sát hay nguy cơ mới trong một khoảng thời gian xác định. Kiểm tra điều khoản WHO và quyền dùng cho đồ án/demo trước khi tải STEPS.
2. Kiểm kê số ca đủ điều kiện, nhãn, tỷ lệ thiếu và ý nghĩa/đơn vị từng cột từ microdata; không đặt 15 thuộc tính làm điều kiện bắt buộc. Nếu dùng STEPS, xem cấu trúc cụm, phân tầng, trọng số `wstep1/2/3` và cơ chế thiếu dữ liệu khi báo cáo/đánh giá.
3. Chia train/validation/test theo người và thời gian hoặc địa điểm phù hợp trước khi fit imputer, scaler, chọn biến hoặc tái lấy mẫu. Với cohort dọc, tránh đưa dữ liệu sau baseline vào đầu vào và xử lý mất theo dõi. Ghi nhận phân bố từng nhóm và số ca dương.
4. So sánh CNN 1D theo assignment với Logistic Regression và baseline phù hợp trên cùng tập test; báo ROC-AUC, PR-AUC, sensitivity, specificity, calibration và khoảng bất định. Không chọn ngưỡng từ test.
5. Kiểm định ngoài bằng dữ liệu Việt Nam độc lập, rà soát chuyên môn và điều kiện sử dụng trước khi đưa bất cứ mô hình nào vào luồng xử lý người dùng thật. Giữ các kết quả hiện có là demo học thuật trong thời gian chờ.
