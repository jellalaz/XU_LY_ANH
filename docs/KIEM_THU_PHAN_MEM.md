# Kiểm tra MorphoLab 1.2

Ngày kiểm tra: 08/11/2026, Windows, Python trong env Miniconda `ai`, Fiji tại `C:/Tools/Fiji`.

## Kết quả

29 kiểm thử chạy qua: 22 kiểm thử thuật toán, chỉ số, phiên làm việc và hủy tác vụ; 7 kiểm thử luồng giao diện Tk thực. Các kiểm thử tích hợp gọi Java và MorphoLibJ thật. Cửa sổ kiểm thử tự đóng, không cần giữ app hay JVM chạy nền.

| Phần | Kiểm tra và kết quả |
| --- | --- |
| Hình thái học | Co, giãn, mở, đóng đối chiếu SciPy, gồm phần tử bất đối xứng và biên ảnh |
| Reconstruction | Đối chiếu scikit-image trên ảnh xám ngẫu nhiên, liên thông 4/8, kiểm tra điểm bất động |
| Distance transform | So với SciPy, gồm ảnh rỗng và ảnh toàn tiền cảnh, có khung nền |
| Connected components | Liên thông 4/8, ảnh đường chéo, không phụ thuộc số ID |
| Watershed | Nhãn không ra ngoài mask, giữ marker, đối chiếu thư viện và Fiji; không yêu cầu mọi pixel biên đồng mức phải giống |
| Chỉ số | Hoán vị ID, gộp/chia vật thể, ảnh rỗng, kích thước sai; IoU/Dice và đếm do Java tính độc lập |
| GUI và cấu hình | Chọn từng mục bằng combobox thực, giữ mã nội bộ khi lưu/nạp JSON; khóa tham số khi đang xử lý |
| Kết quả rỗng / chưa cập nhật | Mẫu 7 vật thể cho F1=1; diện tích tối thiểu 100.000 cho 0 vật thể và F1=0; cảnh báo nguyên nhân; thiếu nhãn đúng hiển thị dấu — |
| Sửa marker | Thêm điểm, chặn xuất khi chưa áp dụng, tính lại, khôi phục tự động; bật sửa marker sẽ thoát Zoom/Pan |
| Fiji và lưu phiên | Gọi plugin thật cho mẫu, xuất CSV/HTML, khôi phục ảnh/nhãn/cấu hình/Fiji; nạp nhãn sai kích thước không làm hỏng kết quả cũ |
| Xử lý thư mục | Ảnh RGB PNG và TIFF xám chạy được; nhãn `_gt` được ghép; không gán F1 khi thiếu nhãn; tệp 3D không hỗ trợ ghi lỗi riêng |
| Benchmark | Một ảnh × 4 phương pháp × 2 bản, xuất đủ 8 cấu hình |
| Khảo sát h | Chỉ dùng validation; chạy đúng bản cài đặt đang chọn, lưu cấu hình hmax kể cả khi ban đầu đang chọn CCL |
| Nghiên cứu | Luồng GUI compare chạy đủ 4 backend trên một ảnh; ablation/robustness và nhiễu cố định được kiểm tra ở phần lõi |
| Hủy / đóng | Hủy worker, không gọi callback sau đóng; tiến trình con được dừng và thu hồi; nghiên cứu dở ghi trạng thái cancelled |

## Cách chạy lại

Kiểm thử phần lõi, không mở giao diện:

```powershell
conda activate ai
python -B -m unittest discover -s tests -v
```

Mặc định 7 kiểm thử Tk được bỏ qua. Để chạy đủ trên máy có Tk và Fiji:

```powershell
$env:MORPHOLAB_DESKTOP_TEST = '1'
python -B -m unittest discover -s tests -v
Remove-Item Env:MORPHOLAB_DESKTOP_TEST
```

Các kiểm thử GUI dùng thư mục tạm riêng, chạy thật các callback và worker; không tải lại dataset và không ghi đè số liệu nghiên cứu cũ. Xem `tests/test_gui_integration.py`.

## Sửa đổi sau rà soát

- Thuật ngữ có giải thích tiếng Việt tại lựa chọn, tiêu đề và bảng; thêm gợi ý khi rê chuột.
- Giao diện tối đồng nhất, nhóm tham số theo bước, thanh trạng thái và nút chạy được dành chỗ; thanh công cụ biểu đồ đồng bộ màu.
- Thông báo rõ kết quả rỗng, thiếu nhãn đúng, thay tham số chưa chạy lại và marker chưa áp dụng. Không cho xuất/đối chiếu nhầm kết quả cũ.
- Khi nạp ảnh mới hoặc tính lại, xóa ghi chú Fiji cũ; đánh giá lại cần chạy Fiji tương ứng.
- Sửa khảo sát h: trước đây luôn đo library nhưng có thể xuất cấu hình custom/CCL; hiện đo đúng engine, cố định hmax và xuất đúng cấu hình đó.

## Giới hạn và ý nghĩa với bài tập lớn

Kiểm thử phần mềm không chứng minh phân đoạn đúng mọi ảnh. Đây là phương pháp dựa trên độ sáng và hình thái, không có nhận dạng ngữ nghĩa hay huấn luyện mô hình AI. Quy trình Fiji độc lập có các quy ước khác Python; chênh lệch chất lượng không chỉ do Watershed.

Số liệu nghiên cứu trên 50 ảnh test và các khảo sát validation đã ghi riêng trong `THUC_NGHIEM.md`. Đợt kiểm thử giao diện này không thay thế phép đo chất lượng trên tập test và không sửa các kết quả đã công bố.

Ứng dụng hỗ trợ thao tác, minh họa và tái lập thí nghiệm. Nội dung chính để nộp vẫn là lý thuyết, cài đặt thuật toán, kiểm chứng Fiji, thiết kế/phân tích thực nghiệm, báo cáo khoảng 30 trang và slide khoảng 10 trang. Đề bài không bắt buộc ứng dụng tích hợp hoặc quy định điểm cộng riêng cho giao diện. Báo cáo cuối kỳ và bộ slide hoàn chỉnh chưa được tạo trong đợt sửa phần mềm này.
