# Biên bản kiểm tra bộ bàn giao — 10/11/2026

## Hồ sơ chính

- Báo cáo biên dịch LaTeX thật: `BAO_CAO_NHOM_1.pdf`, nguồn `latex/main.tex` và `latex/fiji_manual.tex`; giữ font và định dạng học thuật như bản trước.
- Thực hành Fiji từ ảnh gốc, có ảnh từng bước và giải thích lựa chọn, đứng trước chương code Python.
- App nằm ở chương cuối như phần mở rộng dùng chung thuật toán.
- 10 slide, kịch bản 900 giây gồm phần thao tác ngắn, ghi chú có nguồn.
- Đã bỏ Word cũ, nguồn Markdown báo cáo cũ, các bộ chuyển Word/PDF và bản LaTeX chương trùng để tránh nhầm phiên bản.

## Kiểm chứng lần thực hành Fiji làm tay

TIFF và ảnh chụp người học cung cấp được lưu trong `docs/evidence/fiji_manual`, kèm hash và `verification.json`:

| Kiểm tra | Kết quả |
| --- | --- |
| Vùng liên thông trước tách | 5 |
| Marker / nhãn cuối | 7 / 7 |
| IoU GUI Fiji | 0,980451 |
| IoU Python chấm TIFF Fiji | 0,9804508907 |
| Dice GUI Fiji | 0,990129 |
| Dice Python chấm TIFF Fiji | 0,9901289604 |
| F1 đối tượng, IoU ghép ≥ 0,5 | 1,0; TP=7, FP=0, FN=0 |
| Hai mask dùng GUI so ID dương của nhãn gốc | Trùng hoàn toàn |
| Địa hình dùng trong báo cáo | `-distance`, float32 |

Phát hiện file `15_elevation.tif` người học lưu vẫn dương. Giữ bản lưu đó dưới tên `elevation_saved_before_multiply.tif`, xuất lại elevation âm và kiểm chứng bằng JAR MorphoLibJ thật. Nhãn chạy lại từ địa hình âm trùng vùng nhãn làm tay sau ghép ID; địa hình dương khác 1915 pixel. Không thay nhãn dự đoán hoặc nhãn đúng để tăng điểm.

Đối chiếu mảng toán tử xác định bán kính học thử: erosion r=1, dilation r=3, opening/closing r=2, seed tái tạo r=4. Báo cáo ghi rõ, không so như cùng bán kính. Baseline native tự động và Python mặc định giữ số liệu cũ, không thay bằng số làm tay.

## Kiểm thử và tài liệu

- Chú thích/docstring tiếng Việt cho 15 module Python; kiểm tra AST sau khi bỏ docstring: câu lệnh thực thi giữ nguyên.
- Chạy lại bộ test: phát hiện 29, 22 chạy qua, 7 test desktop bỏ qua theo cấu hình mặc định. Không tuyên bố vừa chạy lại đủ test desktop; lần kiểm tra đầy đủ trước đó vẫn lưu ở `unittest.txt`.
- Hai test tích hợp gọi Fiji/Java thật chạy qua. Lượt đầu Windows chặn DLL TkAgg; chạy lại cùng env với quyền thực thi của công cụ đã qua, không đổi code thuật toán.
- Báo cáo: kiểm tra log không tràn lề, không thiếu glyph hoặc tham chiếu; trích mã khớp AST; render trang để xem bố cục. Số trang/hash ghi trong `latex_validation.json`.
- Slide: kiểm tra package, kích thước, bảng/biểu đồ sửa được, font, nhập lại bằng Artifact Tool; render và xem toàn bộ. Không tuyên bố đã mở sửa/lưu lại trong PowerPoint. Người trình bày nên thử trên máy chiếu.
- Ba ảnh thật chạy lại qua 4 cách trong đợt trước cho 12/12 kết quả khớp CSV báo cáo. Đợt này giữ nguyên nghiên cứu 50 test × 4 cách và hai khảo sát 42 dòng, không chạy lại để chọn số đẹp.

## Giới hạn và nộp bài

Khảo sát bổ sung mới dùng 6 validation; một bộ dữ liệu thật; marker nhạy và Python tự cài chưa nhanh bằng thư viện. CCL tốt hơn baseline trong khảo sát, queue Python chậm hơn SciPy trong benchmark. Các kết quả bất lợi được giữ nguyên.

Một đại diện kiểm tra tên/MSSV, phân công thực tế và nộp LMS ghi Nhóm 1 trước hạn trong đề. Chưa tự động nộp LMS. Mức độ hiểu và khả năng giải thích của nhóm là phần phải luyện trước bảo vệ.
