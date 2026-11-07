# Kết quả kiểm chứng và benchmark MorphoLab

Đo ngày 08/11/2026 bằng env Miniconda `ai` của máy hiện tại, Python 3.11.18. Tham số và môi trường đầy đủ lưu trong các file `experiment.json` dưới `docs/evidence`. Đây là các phép đo của phiên bản bàn giao; không phải điểm số được công bố bởi Broad Institute.

## Kiểm tra độ đúng triển khai

14 bài kiểm tra tự động đã qua, gồm morphology với SE bất đối xứng và biên ảnh, reconstruction ảnh xám và tính ổn định, EDT chính xác, liên thông 4/8, h-maxima, Watershed, ảnh rỗng, đổi ID nhãn, split/merge, hai engine và hai bài tích hợp gọi Fiji thật. Không dùng mock để thay thế Fiji. Lệnh:

```bat
python -m unittest discover -s tests -v
```

Kiểm tra tích hợp xác nhận IoU/Dice và số đối tượng do Java/ImageJ tính khớp Python trên cùng ảnh nhãn. Workflow Fiji độc lập cũng xuất các bước co, giãn, mở, đóng, reconstruction, components, distance và marker.

## Ảnh tổng hợp

Tạo 18 ảnh 192×192 với seed cố định 20261108; 6 ảnh validation, 12 ảnh test. Ground truth gồm các đĩa có bán kính biến thiên; vùng giao được phân cho tâm có khoảng cách chuẩn hóa nhỏ nhất. Ảnh có Gaussian blur, biến thiên sáng và ba mức nhiễu. Đây là dữ liệu hình học tổng hợp, không đại diện đầy đủ mô tế bào.

Benchmark kiểm tra trên 3 ảnh validation đầu, 1 warm-up và 2 lượt đo mỗi cấu hình:

| Phương pháp | Macro F1 đối tượng custom | Macro F1 library | Thời gian custom (s) | Thời gian library (s) |
| --- | --- | --- | --- | --- |
| CCL | 0.7210 | 0.7210 | 1.0444 | 0.0411 |
| Raw Watershed | 0.7220 | 0.7220 | 0.7999 | 0.0308 |
| h-maxima | 0.9804 | 0.9804 | 1.0775 | 0.0443 |
| Adaptive | 0.9804 | 0.9804 | 0.9040 | 0.0359 |

F1 ghép đối tượng tại IoU ≥ 0.5. Các phép đo custom ưu tiên khả năng giải thích thuật toán; bản thư viện tận dụng các triển khai native. Không coi chênh lệch thời gian giữa hai bản là một thuật toán mới do nhóm phát minh. Pipeline vẫn tính các ảnh trung gian để phục vụ giao diện, kể cả ở baseline CCL.

Chức năng xử lý thư mục cũng đã chạy thành công trên toàn bộ 18 ảnh tổng hợp; bảng kết quả từng ảnh nằm trong `evidence/synthetic_all.csv`.

## BBBC039 và chọn tham số

BBBC039v1 có 200 ảnh nhân tế bào U2OS 520×696, nhãn thủ công và phân chia chính thức. Phần mềm giữ 100 training, 50 validation và 50 test. Nguồn và giấy phép CC0: [Broad Institute](https://bbbc.broadinstitute.org/BBBC039).

Khảo sát h trên 6 ảnh validation đầu, engine library/hmax, giữ các tham số khác theo `configs/default.json`:

| h | Macro F1 validation |
| --- | --- |
| 0.5 | 0.5546 |
| 1 | 0.6624 |
| 2 | 0.6664 |
| 4 | 0.6501 |
| 6 | 0.6314 |

Chọn h=2 trước khi chạy test. Quy trình chọn này chỉ khảo sát một tham số trên một phần validation; chưa phải tối ưu toàn bộ pipeline. `evidence/selected_parameters.json` giữ cấu hình đã chọn.

## Đánh giá toàn bộ 50 ảnh test BBBC039

Đã chạy đủ bốn phương pháp bằng bản library, mỗi cấu hình 1 warm-up và 2 lượt đo. Thời gian loại đọc/ghi và tính metric; số liệu tổng hợp là macro mean theo ảnh, thời gian là median các median theo ảnh.

| Phương pháp | F1 đối tượng | IoU tiền cảnh | Sai số đếm trung bình | Thời gian (s) |
| --- | --- | --- | --- | --- |
| CCL | 0.8074 | 0.8954 | 24.02 | 0.5822 |
| Raw Watershed | 0.1681 | 0.8954 | 356.50 | 0.4552 |
| h-maxima | 0.7054 | 0.8954 | 21.10 | 0.6193 |
| Adaptive | 0.7038 | 0.8954 | 20.84 | 0.5405 |

![Benchmark BBBC039](evidence/test_bbbc039/benchmark.png)

IoU tiền cảnh giống nhau vì các phương pháp dùng chung mask và không tạo dams. Raw tạo nhiều marker nên chia quá nhiều. h-maxima giảm sai số đếm so với CCL trên tập này nhưng F1 thấp hơn CCL: số đếm tổng thể gần đúng hơn không đồng nghĩa tách đúng từng vật thể. Adaptive chưa vượt h-maxima về F1. Cần xem lỗi cụ thể, điều chỉnh tiền xử lý và marker trên validation trong các nghiên cứu tiếp theo; không dùng kết quả test để tiếp tục chọn rồi báo lại cùng test như một phép đánh giá độc lập mới.

Hai bản custom/library còn được benchmark trên 2 ảnh validation thật để kiểm tra sự nhất quán và chi phí tính toán. F1 hmax lần lượt 0.6304 và 0.6221; cùng IoU tiền cảnh 0.8778, có chênh lệch ranh giới do xử lý plateau và sai số số thực. Chưa chạy bản custom trên toàn bộ 50 ảnh test. Bảng chi tiết nằm trong `evidence/validation_bbbc039`.

## Đối chiếu Fiji

Với ảnh tổng hợp đầu tiên, giao thức chung elevation/marker/mask đạt độ đồng thuận pixel khoảng 98.48% trong hợp tiền cảnh sau ánh xạ ID. Python và Fiji đều tìm được 7 đối tượng, F1 theo ground truth là 1 trên ảnh này. Khác biệt ranh giới vẫn được giữ trong bản đồ disagreement, không bị che bằng việc so sánh số đếm đơn thuần.

Workflow Fiji độc lập trên cùng ảnh tìm 7 đối tượng, IoU tiền cảnh khoảng 0.9801, Dice khoảng 0.9900 do Java tính. Workflow này dùng SE vuông, lượng tử hóa 8-bit, ImageJ Otsu/EDM và extended maxima; không gọi chênh lệch đầu ra là sai lệch của riêng Watershed. Thời gian native pipeline bao gồm xuất ảnh trung gian, không so trực tiếp với thời gian xử lý Python đã loại IO.

## Tái lập và giới hạn

- `docs/evidence` giữ CSV từng ảnh, summary, biểu đồ và metadata của các thí nghiệm thành công. Dữ liệu ảnh tải lại qua `python -m morpholab dataset bbbc039`.
- So sánh Fiji trên ảnh mẫu và test tích hợp đã được thực hiện; chưa chạy Fiji trên toàn bộ test BBBC039.
- Thời gian phụ thuộc tải máy; các đợt đo có thể chạy đồng thời trong quá trình kiểm chứng. Muốn dùng số thời gian để kết luận tối ưu trong báo cáo, nên đo lại tuần tự trên máy rảnh với nhiều lần lặp hơn.
- Chưa có ablation đầy đủ cho mọi phép hình thái hoặc tối ưu tham số đa chiều. Ứng dụng đã có chức năng để mở rộng thực nghiệm này.
- Báo cáo 30 trang, slides và nộp LMS chưa thuộc phần sản phẩm đã hoàn thành trong lần xây phần mềm này.
