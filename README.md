# Xử lý ảnh PTIT — Nhóm 1

**Đề tài:** Phân đoạn đối tượng bằng hình thái học toán học và Watershed. Dùng **Fiji/ImageJ + MorphoLibJ** làm nền tảng tham chiếu, **Python** để tự cài và đánh giá. Không huấn luyện mô hình học sâu.

## 1. Đọc và thực hành theo thứ tự

1. [Báo cáo chính PDF](submission/BAO_CAO_NHOM_1.pdf): lý thuyết → Fiji làm tay có ảnh từng bước → Python và đối chiếu → thực nghiệm → app mở rộng.
2. [Hướng dẫn Fiji đầy đủ](submission/HUONG_DAN_FIJI_DAY_DU.md), có [bản PDF](submission/HUONG_DAN_FIJI_DAY_DU.pdf).
3. [Chạy Python và kiểm thử](submission/HUONG_DAN_CHAY_VA_TEST.md), [kiểm chứng ảnh thật](submission/KIEM_CHUNG_BAO_CAO.md).
4. [10 slide](submission/PRESENTATION_NHOM_1.pptx) và [kịch bản 15 phút](submission/THUYET_TRINH.md), gồm thao tác ngắn trong Fiji và VS Code.
5. [Nguồn LaTeX](submission/latex/README.md), [ZIP để mở Overleaf](submission/NGUON_LATEX_NHOM_1.zip), [đối chiếu yêu cầu thầy](docs/DOI_CHIEU_YEU_CAU.md).

**Bản nộp chính là PDF LaTeX.** Đã bỏ bản Word và bộ chuyển đổi cũ để tránh nhầm phiên bản. Một đại diện nhóm kiểm tra rồi nộp link LMS, ghi Nhóm 1; hạn đề bài là 19/11, kiểm tra giờ đóng bài trên LMS. Chưa tự động nộp.

## 2. Thư mục nào dùng làm gì?

| Thư mục | Vai trò |
| --- | --- |
| `morpholab/` | Code nghiên cứu có chú thích tiếng Việt. `gui.py`, `ui.py` là phần giao diện; phần còn lại phục vụ xử lý, đánh giá và thí nghiệm |
| `fiji/` | Java gọi MorphoLibJ thật, Groovy chạy trong Fiji |
| `configs/` | Tham số xử lý, không phải code thuật toán |
| `data/` | Ảnh đầu vào và nhãn đúng; bộ lớn được Git bỏ qua, có lệnh tải lại |
| `docs/evidence/` | CSV/JSON và minh chứng nghiên cứu cần giữ |
| `docs/evidence/fiji_manual/` | TIFF và ảnh chụp người học làm tay, bảng Fiji và đối chiếu Python |
| `outputs/` | Kết quả chạy cục bộ, mỗi lần chạy dùng thư mục con; không push cả thư mục |
| `tests/` | Kiểm thử tính đúng và tích hợp |
| `scripts/` | Chạy kiểm chứng, tạo hình, dựng tài liệu; không cần chạy hết từng file |
| `submission/` | Báo cáo, slide và hướng dẫn cuối cùng |
| `materials/` | Nguồn giáo trình và tài liệu tham khảo; bản tải nằm trong thư mục con |
| `build/` | Java đã biên dịch, tự tạo lại khi gọi Fiji |

## 3. Chạy nghiên cứu bằng VS Code, không mở app

Mở thư mục project. Trong **Command Prompt** của VS Code hoặc Anaconda Prompt:

```bat
conda activate ai
python -m morpholab segment docs\evidence\fiji_manual\input_16bit.tif --truth docs\evidence\fiji_manual\ground_truth.tif --out outputs\python_01
```

Nếu CMD chưa nhận conda, kích hoạt bằng:

```bat
C:\Users\Admin\miniconda3\condabin\conda.bat activate ai
```

Nếu dùng PowerShell và profile bị chặn, gọi thẳng Python, không cần đổi chính sách máy:

```powershell
& "$env:USERPROFILE\miniconda3\envs\ai\python.exe" -m morpholab segment docs/evidence/fiji_manual/input_16bit.tif --out outputs/python_01
```

Kết quả nằm trong `outputs/python_01`. Xem `overlay.png`, `objects.csv`, `metrics.json` khi có nhãn đúng. TIFF nhãn chứa ID dùng tính điểm; màu PNG/LUT chỉ để xem.

Chấm độc lập nhãn Fiji đã làm tay:

```bat
python -m morpholab evaluate docs\evidence\fiji_manual\ground_truth.tif docs\evidence\fiji_manual\labels.tif --out outputs\manual_metrics.json
```

Kỳ vọng 7 nhãn, F1=1 tại IoU ghép ≥0,5; IoU tiền cảnh 0,98045089, Dice 0,99012896. Điểm này chỉ của ảnh minh họa, không phải toàn bộ dữ liệu.

## 4. Chạy Fiji trực tiếp

Mở `C:\Tools\Fiji\fiji-windows-x64.exe`, dùng menu theo Chương 3 báo cáo. Nếu muốn chạy lại bước Watershed, mở ba TIFF `elevation`, `markers`, `mask` trong `docs/evidence/fiji_manual`: Input=elevation, Marker=markers, Mask=mask, Compactness=0, bỏ Binary markers/Calculate dams/Use diagonal connectivity.

Sau khi hiểu menu, dùng **File → New → Script**, chọn Groovy:

- `fiji/ReplayWatershed.groovy`: chạy lại bước Watershed từ ba TIFF.
- `fiji/Full_Pipeline_Tutorial.groovy`: chạy từ ảnh gốc theo cấu hình native cố định, thư mục đầu ra mới và trống.

Lưu ý minh chứng: file elevation người học lưu trước phép nhân vẫn dương đã được giữ để truy vết. `docs/evidence/fiji_manual/elevation.tif` là bản `-distance` đã xuất lại và kiểm chứng: nhãn chạy lại khớp vùng nhãn làm tay. Bán kính các ảnh học thử được ghi riêng trong `verification.json`.

## 5. Kiểm thử và thí nghiệm nhiều ảnh

```bat
python -B -m unittest discover -s tests -v
python scripts/academic_smoke.py
python -m morpholab dataset bbbc039
python scripts/check_report_examples.py --limit 3 --out outputs/kiem_chung_3anh_01
```

Unit test mặc định bỏ qua 7 test desktop, chạy 22 test còn lại. Hướng dẫn có cách bật test desktop khi cần. Script kiểm chứng ba ảnh tạo `index.html` và so 12 kết quả với CSV đã dùng trong báo cáo; PASS nghĩa khớp số liệu cũ, không phải phân đoạn đúng 100%.

Nghiên cứu chính: 50 test BBBC039 × 4 cách = 200 dòng; 5.720 đối tượng thật. Hai khảo sát bổ sung dùng 6 validation × 7 biến thể mỗi đợt. CSV nằm trong `docs/evidence/v2_*`. Có kết quả bất lợi được giữ nguyên: CCL tốt hơn baseline hmax trong khảo sát, queue Python chưa nhanh hơn SciPy. Không trộn Fiji làm tay, Fiji shared, Fiji native hoặc dữ liệu nhiễu thành cùng một thí nghiệm.

## 6. App là phần mở rộng

Chỉ sau khi đã hiểu phần trên, có thể mở `launch_app.cmd` hoặc `python -m morpholab gui`. Giao diện dùng chung thuật toán với CLI, hỗ trợ chọn ảnh, xem từng bước, khảo sát và lưu phiên. [Hướng dẫn app](docs/HUONG_DAN.md).

## Thành viên và môi trường

| Mã sinh viên | Họ tên |
| --- | --- |
| B23DCCN254 | Kiều Trường Giang |
| B23DCCN667 | Trần Đỗ Lan Phương |
| B23DCCN814 | Giang Thùy Tiên |
| B23DCCN954 | Phạm Văn Vỹ |

Python 3.11 trong env `ai`, thư viện ở `requirements.txt`, phiên bản đã đo ở `requirements-lock.txt`; Fiji gồm JDK và MorphoLibJ 1.6.5. Repository: [jellalaz/XU_LY_ANH](https://github.com/jellalaz/XU_LY_ANH).
