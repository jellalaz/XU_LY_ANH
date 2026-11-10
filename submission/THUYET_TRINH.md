# Kịch bản thuyết trình 15 phút

10 slide, tổng 900 giây. Thời gian gồm thao tác ngắn ở slide 4 và 6; không chạy lại toàn bộ 50 ảnh tại lớp. Luyện đọc và bấm thử để điều chỉnh tốc độ nói, không cố đọc nguyên văn mọi ghi chú. Khi hết 15 phút chuyển sang hỏi đáp.

## Slide 1: Đề tài và mục tiêu

0:00–0:45 — 45 giây.

Nhóm 1 nghiên cứu phân đoạn đối tượng bằng hình thái học toán học và Watershed. Đầu vào là ảnh xám hai chiều; đầu ra là ảnh nhãn, nền 0, mỗi ID dương tương ứng một đối tượng. Bài toán cần tách các vật đang chạm nhau, không chỉ phát hiện vật sáng trên nền tối.

Bài trình bày đi từ lý thuyết tới thao tác tay trong Fiji, sau đó là Python tự cài, kiểm chứng và số liệu nhiều ảnh. App được giới thiệu cuối như một cách thao tác thuận tiện. Đây là xử lý ảnh cổ điển, không huấn luyện mô hình học sâu.

Nguồn: đề bài; báo cáo LaTeX của nhóm.

## Slide 2: Hình thái học và phần tử cấu trúc

0:45–2:25 — 100 giây.

Phần tử cấu trúc là tập vị trí lân cận được dùng để tính giá trị mới cho pixel tâm. Square radius 1 có kích thước 3×3, radius 4 là 9×9. Mỗi cửa sổ chỉ tính một pixel đầu ra, ảnh không bị thu nhỏ kích thước.

Co lấy MIN, giãn lấy MAX theo giá trị pixel. Với vật 255 và nền 0, co chỉ giữ tâm trắng khi toàn bộ lân cận được xét đều trắng; giãn chỉ cần có một pixel trắng. Opening là co rồi giãn, thường loại chi tiết trắng nhỏ. Closing là giãn rồi co, thường khép khe tối và có thể nối hai vật gần nhau.

Mở bằng tái tạo dùng phần còn lại sau co làm seed, ảnh ban đầu làm mask. Nó lan tới ổn định trong mask, khôi phục vùng liên thông còn seed và loại vùng mất hết seed. Opening thường không bảo đảm giữ nguyên hình dạng. Hình minh họa trên slide dùng cùng Square radius 1 để so phép toán công bằng.

Nguồn: morpholab/algorithms.py; hình morphology.png từ Fiji native; https://imagej.net/plugins/morpholibj.

## Slide 3: Fiji từ ảnh gốc tới mask

2:25–4:05 — 100 giây.

Mở synth_00.tif, kích thước 192×192, một kênh 16-bit, và giữ ảnh gốc. Trên bản sao, khoảng dữ liệu là 2749–64456, chuyển về 8-bit theo quy tắc đã ghi. Đây là lượng tử hóa có mất thông tin, không phải yêu cầu bắt buộc của Watershed.

Gaussian sigma 1 giảm nhiễu. Trong Threshold chọn Otsu, bật Dark background. Auto tính ngưỡng, vùng đỏ chỉ để xem trước; Apply mới tạo mask vật 255/nền 0. Tái tạo giữ hình dạng vùng còn seed. Fill Holes lấp nền kín bên trong vật. Size Opening loại cả vùng liên thông nhỏ hơn 25 pixel; hai vật đang dính được tính chung diện tích. Analyze Regions chỉ đo, không lọc.

Kết quả CCL có 5 vùng dù ảnh có 7 vật, vì hai cặp chạm nhau bị tính chung. Đây là vấn đề Watershed sẽ giải quyết. Các ảnh thực hành có thử nhiều bán kính được ghi riêng trong báo cáo, không trộn với bộ đối chiếu cùng bán kính trên slide trước.

Nguồn: TIFF và nhật ký trong docs/evidence/fiji_manual.

## Slide 4: Distance, marker và Watershed trong Fiji

4:05–5:55 — 110 giây, gồm khoảng 35 giây thao tác.

Distance Map tính khoảng cách từ pixel trong vật tới nền gần nhất. Vùng sáng gần tâm có khoảng cách lớn, không phải ảnh bị làm mờ. Đặt EDM output 32-bit để giữ các giá trị lẻ. Extended Maxima với h=2 loại những đỉnh nông; h không phải số lượng vật hay ngưỡng sáng tuyệt đối. Gán nhãn các cực đại thành 7 marker.

Tạo địa hình E=-D để tâm thành vùng thấp. Trong MorphoLibJ, chọn Input=elevation, Marker=ảnh ID và Mask=mask sạch. Đặt compactness 0, bỏ Binary markers, Calculate dams và Use diagonal connectivity. Thu được 7 nhãn. Nêu rằng file elevation lưu trước phép nhân đã được phát hiện và xuất lại; nhãn làm tay khớp lần chạy lại trên địa hình âm.

Thao tác: mở ba TIFF trong docs/evidence/fiji_manual, gọi Marker-controlled Watershed và kiểm tra các trường trước OK. Nếu hết thời gian, dùng ảnh đã lưu và chỉ vào bảng 7 nhãn. Không thay marker bằng ground truth để ép kết quả.

Nguồn: docs/evidence/fiji_manual/verification.json và ảnh manual_watershed.png.

## Slide 5: Định lượng ngay trong Fiji

5:55–7:35 — 100 giây.

Ta nhân bản nhãn đúng và nhãn dự đoán, chuyển các ID dương thành một lớp tiền cảnh 255, nền 0. Không dùng Otsu trên các ID vì số nhãn không phải cường độ vật thể. Dùng Label Overlap Measures đo Jaccard và Dice. Bảng chụp trực tiếp trong Fiji cho IoU 0,980451 và Dice 0,990129.

Python đọc đúng TIFF làm tay và tính lại hai chỉ số, khớp trong sai số hiển thị. Với hai ảnh nhãn gốc, Python còn ghép từng vật tại IoU≥0,5: 7 cặp đúng, không dự đoán thừa hoặc bỏ sót, F1=1. Điều đó không có nghĩa mọi pixel đúng, vì IoU vẫn thấp hơn 1.

Phân biệt bảng tiền cảnh có một nhãn 255 với bảng hình học có 7 đối tượng. LUT chỉ đổi màu hiển thị; trước đó Spectrum làm nhãn 7 và nền cùng màu đỏ nhưng đối tượng không hề mất. Cần đọc giá trị pixel và bảng nhãn thay vì suy luận bằng màu.

Nguồn: ui_overlap.png, fiji_foreground_metrics.csv, verification.json trong bộ minh chứng Fiji làm tay.

## Slide 6: Cài Python và kiểm chứng

7:35–9:15 — 100 giây, gồm khoảng 25 giây mở code/lệnh.

algorithms.py chứa hình thái nhị phân tự cài, gán nhãn BFS, reconstruction bằng hàng đợi, EDT tách trục bằng bao dưới parabol và Watershed dùng heap. Gaussian, Otsu, đọc ghi và thống kê dùng thư viện, được công bố rõ. Code có chú thích tiếng Việt để theo dõi từng bước.

Watershed lan nhãn theo mức ngập lớn nhất trên đường đi; khi hòa dùng thứ tự đến. Pipeline ghép các bước; metrics ghép một-một các đối tượng trước khi chấm. Không cần hai ảnh có cùng màu hoặc cùng thứ tự ID.

Fiji shared nhận cùng địa hình, marker, mask và liên thông để kiểm tra riêng bước Watershed. Fiji native tự xử lý từ ảnh xám, khác ở lượng tử hóa 8-bit, SE vuông và ImageJ EDM, nên là đối chiếu toàn quy trình. Groovy giúp tự động hóa các lệnh sau khi đã hiểu menu.

Thao tác: mở hàm watershed trong VS Code hoặc chạy lệnh evaluate đã chuẩn bị để chấm TIFF Fiji. Không cần mở app.

Nguồn: morpholab/algorithms.py, pipeline.py, metrics.py, fiji.py; fiji/NativePipeline.java.

## Slide 7: Dữ liệu và giao thức

9:15–10:50 — 95 giây.

Ngoài 18 ảnh tổng hợp, nhóm dùng BBBC039 gồm 200 ảnh nhân tế bào U2OS 16-bit, kích thước 520×696 và nhãn đúng. Giữ phân chia chính thức 100 training, 50 validation, 50 test. Không có bước train mạng học sâu; tên split được giữ từ dữ liệu nguồn.

Bảng chính dùng 50 ảnh test với 5.720 đối tượng thật. Bốn cách chạy tạo 200 dòng kết quả, không phải 200 ảnh test độc lập. F1 được lấy trung bình theo ảnh; ghép đối tượng tại IoU≥0,5. Khảo sát từng bước và nhiễu/mờ hiện dùng 6 validation, mỗi đợt 42 dòng; cần nêu giới hạn này.

Ảnh thật trên slide có 156 đối tượng đúng. Python custom dự đoán 187, F1 khoảng 0,7580; Fiji native dự đoán 147, F1 khoảng 0,9571. Có cả ảnh khó: một ảnh khác có 69 đối tượng đúng nhưng Python chỉ dự đoán 23, F1 0,2174. Không chọn toàn ảnh đẹp để minh họa.

Nguồn: https://bbbc.broadinstitute.org/BBBC039; docs/evidence/v2_compare_bbbc039_test/per_image.csv.

## Slide 8: Kết quả trên 50 ảnh test

10:50–12:30 — 100 giây.

F1 trung bình theo ảnh của Python tự cài là 0,7087; Python thư viện 0,7054; Fiji shared 0,7188 và Fiji native 0,8917. Báo cáo có khoảng tin cậy bootstrap 95%, lấy mẫu lại theo ảnh 1.000 lần với seed cố định. CSV từng ảnh, cấu hình và môi trường được giữ để tái lập.

Ba cách đầu có cùng mask nên IoU tiền cảnh đều khoảng 0,8954. Fiji native có IoU khoảng 0,8910 nhưng F1 đối tượng cao hơn. Điều này chứng minh mask vật/nền khớp cao chưa đủ để tách đúng từng đối tượng; biên giữa các vật cũng quan trọng.

Không được kết luận riêng hàm Watershed native tốt hơn, vì toàn bộ tiền xử lý và cách tạo marker khác nhau. Native vẫn có lỗi gộp và không có bằng chứng tổng quát cho mọi miền ảnh. Các khoảng tin cậy là mô tả tập khảo sát, không tự thay kiểm định cặp hoặc đánh giá trên bộ dữ liệu mới độc lập.

Nguồn: summary.csv, per_image.csv và study.json trong docs/evidence/v2_compare_bbbc039_test.

## Slide 9: Khảo sát và benchmark

12:30–14:10 — 100 giây.

Trên 6 ảnh validation, marker chưa lọc cho F1 0,1563 do chia thừa. Lọc bằng h-maxima nâng lên 0,6663, nhưng CCL đạt 0,8168. Như vậy baseline Watershed còn chia thừa, không phải cứ thêm bước là tốt hơn. Bỏ Gaussian đạt 0,6884; làm mờ mạnh sigma 3 làm F1 còn 0,6018. Các kết quả bất lợi đều được giữ trong báo cáo.

Benchmark reconstruction đo 5 lần sau một lượt làm nóng, kiểm tra đầu ra bằng nhau. Trên ảnh 160×160, queue Python khoảng 0,100107 giây, vòng lặp dùng SciPy khoảng 0,030336 giây. Ý tưởng giảm cập nhật chưa chắc nhanh hơn vòng lặp có nhân xử lý biên dịch. Đây là so triển khai, không cô lập độ phức tạp thuật toán.

Bộ kiểm thử có 29 trường hợp được ghi nhận trong lần kiểm tra đầy đủ. Đợt chỉnh chú thích giữ nguyên AST thực thi và chạy lại kiểm thử phù hợp. Hạn chế lớn còn lại là khảo sát 6 validation và chỉ một bộ dữ liệu thật. Hướng tiếp theo là mở rộng khảo sát trước khi tuyên bố cải tiến.

Nguồn: docs/evidence/v2_ablation_bbbc039, v2_robustness_bbbc039 và academic_checks/timing_summary.csv.

## Slide 10: App hỗ trợ và kết luận

14:10–15:00 — 50 giây.

Sau phần nghiên cứu, MorphoLab giúp chọn ảnh, chỉnh tham số, xem các bước và lưu kết quả thuận tiện. Giao diện gọi lại chính pipeline và algorithms của phần chạy Terminal; nó không làm thuật toán chính xác hơn và không thay thế minh chứng nghiên cứu.

Nhóm đã trình bày lý thuyết, tự cài các thuật toán chính, làm tay và đo trong Fiji, đối chiếu bằng Python, đánh giá nhiều ảnh và đo hiệu năng. Giới hạn là độ nhạy với nền, marker, tốc độ Python và phạm vi dữ liệu. Hướng phát triển ưu tiên là khảo sát toàn validation và kiểm tra dữ liệu khác. Kết thúc phần trình bày và chuyển sang hỏi đáp.

Nguồn: morpholab/gui.py; ảnh chụp ứng dụng do người học cung cấp; kết luận báo cáo.
