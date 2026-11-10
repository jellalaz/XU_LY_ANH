# Nguồn báo cáo LaTeX — Nhóm 1

`main.tex` là nguồn chính, `fiji_manual.tex` chứa chương thực hành Fiji từng bước. Chỉnh hai file này khi sửa nội dung; không còn bộ sinh từ Word/Markdown cũ ghi đè nguồn.

Thứ tự báo cáo: giới thiệu, lý thuyết, Fiji làm tay, Python và đối chiếu, thực nghiệm nhiều ảnh, app mở rộng và kết luận. Có bìa, mục lục, danh mục hình/bảng, công thức và tài liệu tham khảo. Đây là bố cục học thuật của nhóm, không phải mẫu chính thức do PTIT ban hành.

## Biên dịch

- **Overleaf:** tải `submission/NGUON_LATEX_NHOM_1.zip`, chọn XeLaTeX và `main.tex`.
- **TeX Live/MiKTeX:** chạy `xelatex -interaction=nonstopmode main.tex` ít nhất hai lần, hoặc `latexmk -xelatex main.tex`.
- **Tectonic:** chạy `tectonic main.tex`; lần đầu cần tải gói. Font Windows: Times New Roman, Arial, Consolas; nguồn có font thay thế khi lên Overleaf.
- **Trên máy phát triển:** `python scripts/build_report.py` từ gốc project, dùng Python có pypdf và Tectonic. Có thể truyền `--tectonic <duong_dan>`. Thư viện dựng tài liệu không phải thư viện bắt buộc để chạy thuật toán.

`scripts/build_report.py` đồng bộ các trích mã thực thi, biên dịch và kiểm tra trước khi chép PDF cuối sang `submission/BAO_CAO_NHOM_1.pdf`. Script không tái tạo nội dung chương từ bản thảo cũ. File trung gian nằm dưới `outputs/latex_build`.

## Hình và dữ liệu

- `figures/manual_*.png`: hình khoa học từ TIFF người học lưu khi làm tay.
- `figures/ui_*.png`: ảnh chụp giao diện do người học gửi, không phải giao diện giả lập.
- Các hình so sánh nhiều ảnh lấy từ CSV/TIFF đã đo, giữ riêng nguồn và phạm vi.
- `code/`: trích thuật toán từ code đang chạy, bỏ chú thích để gọn nhưng kiểm tra AST câu lệnh giống bản gốc. Code chính trong `morpholab/` có chú thích tiếng Việt.

Chạy `python scripts/prepare_manual_evidence.py` để kiểm tra lại TIFF/metric và dựng lại hình thực hành từ bộ dữ liệu đã lưu trong Git. Không cần thư mục Temp hoặc đầu ra cũ của người dùng. Cờ `--capture` chỉ dành cho người quản lý khi nhập lại một buổi thực hành mới, không dùng khi tái lập bản đã nộp.

Nguồn TIFF: `docs/evidence/fiji_manual`. Bản elevation dương lưu trước phép nhân được giữ riêng để truy vết; bản elevation dùng trong báo cáo là `-distance`, đã chạy lại MorphoLibJ và khớp vùng nhãn làm tay. Các ảnh toán tử học thử có bán kính khác nhau, chú thích ghi rõ để tránh hiểu nhầm là thí nghiệm kiểm soát một yếu tố.

Trang bìa không in số, phần đầu dùng số La Mã, nội dung bắt đầu từ 1. Số trang vật lý trong trình xem khác số ở chân trang.
