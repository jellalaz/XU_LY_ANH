# Báo cáo LaTeX — PTIT Nhóm 1

Mở `main.tex`. Tệp PDF xuất cuối cùng ở `../BAO_CAO_NHOM_1.pdf` là bản báo cáo chính, thay bản PDF bố cục cũ. Bản Word tạo trước đó giữ để tham khảo; không đồng bộ bố cục/nội dung mới với bản LaTeX.

Đây là bố cục học thuật A4 tự xây dựng theo nội dung đề bài, không phải mẫu chính thức được PTIT ban hành. Có bìa, tóm tắt, mục lục, danh mục hình/bảng, chương/mục, công thức, bảng/hình có số và tài liệu tham khảo.

## Biên dịch

- **Overleaf:** tải ZIP nguồn LaTeX, chọn **XeLaTeX** làm compiler, chọn `main.tex` là main document, Recompile. Không cần upload code/dataset ngoài thư mục LaTeX này.
- **TeX Live/MiKTeX:** vào thư mục này, chạy `xelatex -interaction=nonstopmode main.tex` hai lần; hoặc `latexmk -xelatex main.tex`. Có thể cần lần thứ ba khi mục lục thay đổi độ dài.
- **Tectonic:** chạy `tectonic main.tex`. Công cụ tự tải gói cần thiết; lần đầu cần mạng. Bản đã biên dịch dùng Tectonic 0.17.0 (engine XeTeX).

Font trên Windows là Times New Roman, Arial, Consolas. Nếu không có, nguồn tự chọn TeX Gyre Termes/Heros và Latin Modern Mono. Các công thức là LaTeX thật, không phải ảnh chụp hoặc văn bản giả công thức.

## Tổ chức nguồn

- `main.tex`: toàn bộ báo cáo, bảng lấy từ CSV đã đo, công thức và trích dẫn.
- `fiji_tutorial.tex`, `app.tex`: nội dung chi tiết để dùng khi dựng lại nguồn bằng script.
- `code/`: các đoạn code thực được đưa vào báo cáo.
- `figures/`: hình khoa học tạo từ dữ liệu thí nghiệm và ảnh giao diện người học đã cung cấp.

`scripts/build_latex_report.py` ở repository tạo `main.tex` từ bản nội dung nghiên cứu và hai phần bổ sung; nó không cần chạy khi bạn chỉnh trực tiếp `main.tex`. `scripts/latex_figures.py` tạo lại hình khoa học từ ảnh/kết quả cục bộ; giữ số liệu nghiên cứu và loại ảnh rõ ràng.

## Số trang

Trang bìa không in số. Phần đầu dùng i, ii, …; nội dung chính bắt đầu từ 1. Trình xem PDF có thể báo số thứ tự vật lý khác số in ở chân trang. Khi dẫn trong báo cáo, dùng số hình/bảng/mục, hoặc số trang in trên bản PDF mới.

Các ảnh minh họa gồm ví dụ Python/Fiji, sáu bước xử lý, toán tử hình thái Fiji, ảnh thật và nhãn đúng, CCL so với Watershed, ba biểu đồ nghiên cứu, thanh công cụ Fiji và giao diện app. Ảnh giao diện do người học cung cấp ở các lượt trước, không dùng để thay dữ liệu định lượng.
