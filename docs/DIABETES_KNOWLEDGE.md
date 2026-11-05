# Phạm vi tri thức đái tháo đường

Rà soát ngày 05/11/2026: `knowledge/sources.json` có các đoạn tiếng Việt nhập thủ công về tổng quan, triệu chứng, chẩn đoán, lối sống, hạ và tăng đường huyết, biến chứng, bàn chân và theo dõi. Những đoạn này cần được chuyên gia y tế rà soát độc lập; ngày ghi trong tài liệu không đồng nghĩa ngày kiểm duyệt.

Danh sách `knowledge/web_sources.json` bổ sung nguồn gốc CDC và NIDDK theo các nhóm sau:

| Nhu cầu | Nội dung nguồn bổ sung |
| --- | --- |
| Hiểu kết quả xét nghiệm | Chẩn đoán, tiền đái tháo đường, HbA1c và giới hạn của xét nghiệm |
| Điều trị và tự quản lý | Insulin, thuốc, theo dõi glucose liên tục, carbohydrate, vận động |
| Tình huống cấp và ngày ốm | Hạ đường huyết, nhiễm toan ceton, kế hoạch khi ốm |
| Biến chứng và theo dõi | Thận, thần kinh, bàn chân, tim mạch và khám theo dõi |
| Nhóm và nhu cầu đặc biệt | Thai kỳ, sau sinh và sức khỏe tinh thần |

Nguồn tự động được chia đoạn, tạo embedding và lưu trong Neo4j khi chạy `knowledge-refresh`; tệp JSON chỉ là danh sách URL, không chứa nội dung đã tải. Kiểm tra log mỗi lần nạp vì một số nguồn có thể thất bại và dữ liệu cũ sẽ được giữ lại. Nguồn web có trạng thái `unreviewed_web`: chat chỉ cung cấp liên kết, không dùng nội dung đó để sinh câu trả lời. Khi câu hỏi có cả nguồn thủ công và web, phần trả lời chỉ dựa trên nguồn thủ công; độ đầy đủ còn phụ thuộc kết quả truy xuất. Vì vậy việc mở rộng nguồn giúp tìm tài liệu tham khảo, chưa bảo đảm chat giải thích sâu hơn cho mọi chủ đề.

Ưu tiên tiếp theo là nhờ chuyên gia rà soát nội dung tiếng Việt theo từng nguồn và ngày cập nhật, đặc biệt xử trí cấp cứu, dùng thuốc, thai kỳ và các ngưỡng xét nghiệm; đánh giá riêng khả năng truy xuất bằng câu hỏi tiếng Việt thực tế. Các khuyến nghị cần được đối chiếu hướng dẫn hiện hành tại Việt Nam, bệnh đồng mắc và hoàn cảnh từng người. Không tự chuyển nguồn web chưa kiểm duyệt thành nguồn được phép sinh câu trả lời chỉ vì đã tải thành công.

Kiểm tra truy xuất sau khi nạp ngày 05/11/2026: câu hỏi về ảnh hưởng của tiểu đường lên thận tìm được trang NIDDK về bệnh thận; câu hỏi về theo dõi sau thai kỳ tìm được trang sau sinh cùng các nguồn khác; câu hỏi ngắn “HbA1c là gì?” không tìm được nguồn ở ngưỡng hiện tại. Đây chỉ là kiểm tra thăm dò, chưa phải đánh giá toàn diện chất lượng truy xuất hay câu trả lời.
