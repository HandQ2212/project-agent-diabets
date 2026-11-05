# Nguồn và cách tái lập dữ liệu NHANES 15 chỉ số

Đây là dữ liệu [NHANES của CDC Hoa Kỳ](https://www.cdc.gov/nchs/nhanes/index.html), **không phải WHO STEPS và không phải dữ liệu Việt Nam**. Nhãn DIQ010 là câu trả lời đã từng được nhân viên y tế thông báo mắc đái tháo đường; không phải nhãn mắc mới. Hệ thống website hiện không sử dụng mô hình do notebook này tạo.

- Notebook có mã đọc, xử lý, huấn luyện và đánh giá: `notebooks/NHANES_15_Chi_So.ipynb`.
- Tệp gốc: `data/raw/nhanes/`, gồm 10 loại DEMO, DIQ, BMX, BPX, GLU, GHB, TCHOL, HDL, TRIGLY, BIOPRO cho hai chu kỳ 2015–2016 (`_I`) và 2017–2018 (`_J`). Không sửa dữ liệu XPT gốc.
- Dữ liệu dẫn xuất đã chia: `data/raw/nhanes15_derived/{train,validation,test}.csv`; chứa mã SEQN công khai, PSU/tầng, 15 biến và nhãn. Các thư mục `data/raw` bị Git bỏ qua; không gửi lại microdata khi chưa xem điều kiện nguồn.
- Artifact: `artifacts/nhanes15_notebook/` gồm trọng số CNN, scaler, Logistic Regression và `report.json`. Artifact bị Git bỏ qua, không được web nạp.
- Bản sao manifest từ lần chạy đã thực hiện: `data/metadata/NHANES15_manifest.json`. Trong đó có URL tải trực tiếp từng file, SHA-256, số lượng mẫu, phiên bản, cấu hình và kết quả. Manifest chỉ có thống kê tổng hợp, không có bản ghi cá nhân. Sau lần chạy mới hãy sao chép report mới để cập nhật snapshot này.

| Mã | Diễn giải | Đơn vị |
| --- | --- | --- |
| RIDAGEYR, RIAGENDR | Tuổi, giới theo mã NHANES | năm; mã 1/2 |
| BMXBMI, BMXWAIST | BMI, vòng eo | kg/m²; cm |
| BPXSY1, BPXDI1 | Huyết áp tâm thu/tâm trương lần đo 1 | mmHg |
| LBXGLU, LBXGH | Glucose huyết tương nhịn đói, HbA1c | mg/dL; % |
| LBXTC, LBDHDD, LBXTR | Cholesterol toàn phần, HDL, triglyceride | mg/dL |
| LBXSATSI, LBXSCR | ALT, creatinine huyết thanh | U/L; mg/dL |
| BMXWT, BMXHT | Cân nặng, chiều cao | kg; cm |

Xem [codebook chu kỳ 2017–2018](https://wwwn.cdc.gov/nchs/nhanes/continuousnhanes/default.aspx?BeginYear=2017) và codebook tương ứng 2015–2016 trước khi sửa tập biến. BMI là biến dẫn xuất từ chiều cao/cân nặng, do đó các biến không độc lập. Các xét nghiệm có thể đã liên quan đến chẩn đoán trong nhãn; dữ liệu đo sau khi đã mắc bệnh có thể chịu ảnh hưởng điều trị. Mục tiêu là minh họa phân loại câu trả lời khảo sát, không phát hiện bệnh, không dự báo mắc mới và không đại diện cho người Việt Nam.

## Tải lại nếu thiếu tệp

Các địa chỉ gốc được liệt kê trong trường `source_urls` của manifest. Có thể dùng Python trên máy có mạng:

```sh
python - <<'PY'
import json
from pathlib import Path
from urllib.request import urlretrieve

manifest = json.loads(Path('data/metadata/NHANES15_manifest.json').read_text())
destination = Path('data/raw/nhanes')
destination.mkdir(parents=True, exist_ok=True)
for filename, url in manifest['source_urls'].items():
    path = destination / filename
    if not path.exists():
        print('Downloading', filename)
        urlretrieve(url, path)
PY
```

Kiểm tra SHA-256 của từng tệp với manifest trước khi coi dữ liệu là cùng phiên bản; URL nguồn có thể được CDC cập nhật. Mở notebook trong Jupyter/VS Code, dùng môi trường có `nbformat`, `ipykernel`, NumPy, pandas, scikit-learn, PyTorch, joblib và hỗ trợ đọc SAS. Chạy toàn bộ cell từ đầu. Kết quả notebook lần chạy hiện tại là Python 3.14 trên máy host; artifact joblib có thể không tương thích môi trường Docker Python 3.11, do đó huấn luyện lại trong môi trường đích nếu sau này cần kiểm thử tương thích. Không tự đưa artifact vào website.

## Nguồn Việt Nam

WHO STEPS Việt Nam 2021 được ưu tiên cho các bước sau, nhưng đường tải microdata trả trang rỗng trong môi trường này. Không gọi dữ liệu, notebook hoặc mô hình hiện tại là WHO/Vietnam. Khi có quyền truy cập và tệp thật, cần xem điều khoản, codebook, trọng số khảo sát và định nghĩa nhãn, thiết kế notebook riêng và kiểm định trước khi cân nhắc thay đổi website. Xem `docs/DATASET_CANDIDATES_VIETNAM.md`.
