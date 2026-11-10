# Tự kiểm chứng báo cáo bằng ảnh thật

Mục đích: chạy lại dữ liệu, xem ảnh và kiểm tra số liệu trong báo cáo. Không cần mở app MorphoLab. Ảnh tổng hợp 7 vật chỉ là ví dụ nhập môn; máy có 200 ảnh BBBC039 và 200 tệp nhãn tương ứng. Bảng chính dùng 50 ảnh test, không phải 200 ảnh test: 50 ảnh × 4 cách xử lý = 200 dòng kết quả.

## 1. Xem ảnh thật ngay

Mở `D:\XU_LY_ANH\data\bbbc039\images` bằng Explorer hoặc File → Open trong Fiji. Tệp cùng tên trong `labels` là nhãn đúng; không dùng nó thay ảnh đầu vào. Mỗi ảnh chứa nhiều đối tượng, không chỉ một hình tròn.

## 2. Chạy kiểm chứng ba ảnh đầu, giữ nguyên tham số báo cáo

Trong **Anaconda Prompt**, chạy từng dòng:

```bat
conda activate ai
cd /d D:\XU_LY_ANH
python scripts\check_report_examples.py --limit 3 --out outputs\toi_test_bao_cao_01
```

Chờ dòng `ALL REPORT VALUES MATCH` và dấu nhắc `(ai)` trở lại. Nếu thư mục đã có dữ liệu, đổi đuôi `_01` thành `_02`; script không ghi đè đợt trước. Không có server chạy ngầm sau khi lệnh kết thúc. Chạy tuần tự từng ảnh; không cần mở thêm app.

Script chạy thật Python tự cài, Python thư viện, Fiji chung đầu vào và Fiji toàn quy trình. Dùng đúng `configs/default.json`, cùng ba ảnh test đầu, rồi so số lượng, IoU, Dice, F1 với CSV đã dùng trong báo cáo, dung sai 1e-9. Không kiểm tra thời gian phải giống lần cũ.

Script này xuất CSV bằng thư viện chuẩn của Python để tránh phụ thuộc pandas ở bước kiểm chứng. Lệnh `study` đầy đủ vẫn dùng pandas; trong lượt chạy từ công cụ ngày 09/11 Windows từng chặn DLL của pandas. Không cần thay thuật toán hoặc tắt chính sách bảo vệ để dùng script kiểm chứng này.

## 3. Mở kết quả để hiểu

Mở `D:\XU_LY_ANH\outputs\toi_test_bao_cao_01\index.html` bằng trình duyệt. Mỗi ảnh có sáu ô: ảnh gốc, nhãn đúng, Python tự cài, Python thư viện, Fiji shared và Fiji native. Cuộn xuống xem đủ ba ảnh.

| Ảnh test, tiền tố tên | Đối tượng đúng | Python tự cài: số dự đoán / F1 | Fiji native: số dự đoán / F1 |
| --- | --- | --- | --- |
| IXMtest_A09_s1 | 156 | 187 / 0.7580 | 147 / 0.9571 |
| IXMtest_A12_s7 | 69 | 23 / 0.2174 | 19 / 0.2273 |
| IXMtest_A16_s2 | 93 | 120 / 0.7042 | 84 / 0.9379 |

Ảnh thứ hai là ca khó có nhiều vật bị bỏ sót hoặc gộp. Giữ nó để phân tích giới hạn, không xóa vì điểm thấp. Màu ID giữa hai ảnh có thể khác dù vùng giống nhau, nên nhìn màu không thay phép ghép đối tượng.

Đọc `check.csv`: cần 12 dòng kết quả, `matches_report=True` cho tất cả. **PASS nghĩa là tái lập đúng kết quả báo cáo**, không có nghĩa phân đoạn đạt 100%. `verification.json` ghi phạm vi và cấu hình. Mỗi thư mục ảnh có TIFF nhãn, JSON điểm, ảnh minh họa và kết quả Fiji.

## 4. Tự bấm lại Watershed trong Fiji trên một ảnh thật

1. Trong folder kết quả chọn ảnh đầu `IXMtest_A09_s1...`, vào `fiji-native`.
2. Mở `elevation.tif`, `markers.tif`, `mask.tif` trong Fiji.
3. Plugins → MorphoLibJ → Segmentation → Marker-controlled Watershed.
4. Input = elevation; Marker = markers; Mask = mask; Compactness = 0. Bỏ Binary markers, Calculate dams và Use diagonal connectivity.
5. Chạy; lưu ảnh nhãn tên mới `manual_labels.tif` trong chính folder `fiji-native`. Không chuyển nhãn sang RGB.
6. Analyze Regions trên ảnh nhãn cho bảng đối tượng. Với ảnh đầu và đúng các tham số trên, kỳ vọng 147 nhãn. Nhãn đúng có 156, nên thuật toán vẫn chưa hoàn hảo.
7. Để chấm kết quả thao tác tay, dùng lệnh `python -m morpholab evaluate <duong_dan_nhan_dung> <duong_dan_manual_labels.tif> --out <duong_dan_json_moi>` trong Anaconda Prompt. Lấy tệp nhãn đúng cùng tên ảnh trong `data\bbbc039\labels`. Các đường dẫn có khoảng trắng cần đặt trong dấu ngoặc kép.

Có thể mở `Run_in_Fiji.groovy` trong folder `fiji-native` bằng Script Editor, chọn Groovy và Run để chạy lại bước Watershed mà không phải chọn ba cửa sổ bằng tay. Script này chỉ chạy lại bước tách; script `fiji/Full_Pipeline_Tutorial.groovy` chạy từ ảnh gốc, được hướng dẫn riêng trong `HUONG_DAN_FIJI_DAY_DU.md`.

## 5. Muốn kiểm chứng toàn bộ 50 ảnh trong bảng báo cáo

```bat
python scripts\check_report_examples.py --limit 50 --out outputs\toi_test_bao_cao_50anh_01
```

Lệnh dài hơn và tạo nhiều ảnh trung gian. Không cần chạy trong buổi thuyết trình. Kỳ vọng 200 dòng kết quả và tất cả khớp CSV báo cáo. Đây là chạy lại cùng test, không phải bổ sung 50 ảnh mới và không dùng để chọn tham số theo nhãn test.

Nguồn số liệu báo cáo: `docs\evidence\v2_compare_bbbc039_test\per_image.csv` và `summary.csv`. F1 trung bình theo ảnh lần lượt khoảng 0.7087, 0.7054, 0.7188 và 0.8917. Nếu chỉ chạy ba ảnh, trung bình ba ảnh sẽ khác trung bình 50 ảnh; không thay bảng báo cáo bằng con số demo nhỏ.

## 6. Kết luận mình có thể trình bày sau khi test

- Có tự cài và chạy được trên ảnh thật, không chỉ ảnh hình tròn.
- Fiji có tạo nhãn bằng MorphoLibJ thật và có thể thao tác lại bằng giao diện.
- Đánh giá bằng nhãn đúng, không chỉ đếm hoặc nhìn ảnh màu.
- Có ca tốt lẫn ca khó; cùng một cấu hình không tối ưu cho mọi ảnh.
- Ảnh minh họa trong báo cáo là ảnh tiêu biểu; CSV từng ảnh là bằng chứng đầy đủ của bảng số liệu.

Hướng mở rộng có ích nhất: khảo sát bỏ/thay từng bước trên toàn bộ 50 validation thay vì 6 ảnh hiện tại. Giữ riêng phần test để đánh giá; không cộng các bản nhiễu/mờ thành ảnh độc lập mới.
