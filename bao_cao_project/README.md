# Hồ sơ báo cáo Project: Dự đoán bệnh tiểu đường

- `Bao_cao_Duong_An.pdf`: báo cáo hoàn chỉnh; bìa gồm tên project, môn học và năm.
- `Bao_cao_Duong_An.tex`: nguồn LaTeX; biên dịch từ thư mục này bằng `xelatex -interaction=nonstopmode -halt-on-error Bao_cao_Duong_An.tex` hai lần.
- `noi_dung/`: nội dung từng phần; `hinh_anh/`: minh chứng, bao gồm các ảnh giao diện lịch sử có ghi rõ thời điểm.
- `../notebooks/training/`: sáu notebook riêng theo bài toán, đã lưu kết quả và biểu đồ; xem `KET_QUA_NANG_CAP.md` trong thư mục đó.
- `../artifacts/notebook_runs/`: kết quả và mô hình của các lần chạy được trích dẫn trong hai bảng kết quả; các lần chạy mới khác mặc định bị Git bỏ qua.
- `notebook/Training_Duong_An.ipynb`: notebook tổng hợp phiên bản cũ, giữ lại để tham khảo.

Mô hình web NHANES 15 chỉ số dùng snapshot riêng `artifacts/nhanes15_web` từ notebook NHANES 15; các kết quả lựa chọn khác trong notebook là thực nghiệm độc lập, không tự cập nhật website. Không có model WHO STEPS hoặc huấn luyện trên người Việt Nam. Các kết quả phục vụ học thuật, không dùng để chẩn đoán, sàng lọc hay điều trị.
