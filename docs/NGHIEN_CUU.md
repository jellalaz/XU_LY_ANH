# Nghiên cứu hình thái học và Watershed

Ghi chú nghiên cứu ban đầu ngày 07/11/2026. Hiện trạng cài đặt và kết quả đo ngày 08/11 được cập nhật riêng trong [hướng dẫn](HUONG_DAN.md) và [thực nghiệm](THUC_NGHIEM.md).

Đề tài nhóm 1 hướng tới tách từng đối tượng trong ảnh, đặc biệt khi các đối tượng chạm nhau. Cần giải thích thuật toán, cài đặt bằng Python và kiểm chứng từng bước bằng MorphoLibJ. Những lựa chọn thí nghiệm dưới đây là đề xuất ban đầu, chưa phải kết quả đo.

## Nền tảng từ slide PTIT

Gọi A là tập pixel tiền cảnh, B là phần tử cấu trúc chứa gốc. Phép co giữ các vị trí mà B đặt lọt trong A; phép giãn mở rộng A theo B. Với quy ước tập hợp, dilation là tổng Minkowski A ⊕ B = {a+b | a thuộc A, b thuộc B}; erosion A ⊖ B = {x | x+B nằm trong A}. Cần xử lý đúng phép phản xạ khi cài dilation với B bất đối xứng.

Opening là co rồi giãn với cùng B; closing là giãn rồi co. Opening có thể loại chi tiết nhỏ và cầu nối hẹp; closing có thể lấp khe nhỏ nhưng cũng có thể nối nhầm đối tượng. Kích thước và hình dạng B quyết định cấu trúc bị thay đổi. Không mặc định hình thái học luôn bảo toàn diện tích hay số đối tượng.

Slide PTIT còn trình bày tách biên A trừ (A ⊖ B), và điền vùng bằng giãn lặp có ràng buộc trong phần bù của đường biên. Nguồn: slide PTIT trong [danh sách tài liệu](../materials/SOURCES.md).

## Reconstruction và điều khiển Watershed

Reconstruction bằng giãn khởi đầu từ marker M nằm trong mask F, lặp X tiếp theo = min(dilation(X), F) đến ổn định. Với ảnh nhị phân, min tương đương giao tập. Marker lan trong mask theo liên thông đã chọn. Có thể dùng reconstruction để điền lỗ, loại thành phần chạm biên và kiểm soát cực trị.

Watershed xem ảnh như địa hình và tạo các lưu vực. Cực trị do nhiễu dễ gây chia quá nhiều vùng; marker và extended extrema giúp kiểm soát việc chia. Với vật thể tròn chạm nhau, một hướng là tạo mask, tính khoảng cách tới nền, đảo địa hình khoảng cách rồi chạy Watershed trong mask. Đầu ra phải giữ nhãn riêng cho mỗi đối tượng.

MorphoLibJ có các biến thể Classic Watershed, Marker-controlled Watershed và Distance Transform Watershed. Manual giải thích reconstruction và extended extrema ở chương 5, Watershed ở chương 6. Nguồn: [manual và trang plugin](../materials/SOURCES.md).

## Workflow đề xuất

1. Chọn ảnh 2D và chuẩn hóa tiền cảnh, kiểu dữ liệu, đơn vị pixel.
2. Tạo mask bằng ngưỡng; lưu cả mask trước và sau xử lý hình thái.
3. Khảo sát opening, closing hoặc reconstruction với phần tử cấu trúc có kích thước được ghi rõ.
4. Tính distance transform và tạo marker từ cực đại có kiểm soát; gán nhãn marker theo liên thông.
5. Chạy marker controlled Watershed trên âm distance map, giới hạn trong mask.
6. Lưu ảnh nhãn, đường phân cách, ảnh overlay, tham số và thời gian chạy.
7. Lặp cùng quy trình trên Fiji và Python; đối chiếu cả các ảnh trung gian.

Connected components cung cấp baseline đếm vùng liên thông. Baseline này chưa tách được hai vật thể vẫn nối nhau trong mask. Có thể bổ sung Watershed không điều khiển marker để minh họa lỗi chia quá nhiều vùng.

## Cài đặt Python đề xuất

Nên có bản thuật toán do nhóm cài đặt và bản dùng thư viện để đối chiếu. Phần tự cài đặt có thể gồm co, giãn, opening, closing, reconstruction bằng hàng đợi, gán nhãn bằng BFS và Watershed bằng hàng đợi ưu tiên. Phải mô tả quy tắc xử lý plateau, pixel đồng mức và đường phân cách của Watershed.

NumPy, SciPy và scikit-image là các ứng viên cho bản đối chiếu; cần xác minh API và cố định phiên bản trước khi lập trình. Chưa chọn dependency hoặc tuyên bố tương đương với MorphoLibJ.

## Kiểm chứng giữa Fiji và Python

Cần ghi cùng phần tử cấu trúc, gốc của nó, quy tắc xử lý biên ảnh, liên thông, mask, marker và kiểu dữ liệu. Giữ thống nhất tùy chọn có hoặc không tạo đường phân cách Watershed.

MorphoLibJ Distance Transform Watershed có các lựa chọn khoảng cách chamfer, chuẩn hóa trọng số, dynamic và liên thông. Dynamic lớn thường giảm số lần chia. Nếu Python dùng khoảng cách Euclid chính xác còn Fiji dùng chamfer, đó là hai cấu hình khác nhau cần được báo cáo rõ. Không mặc định hai nền tảng phải tạo cùng nhãn số.

Đề xuất kiểm tra thuật toán Watershed riêng bằng cách cung cấp chính cùng địa hình, marker và mask cho hai nền tảng. Sau đó mới so sánh toàn pipeline. Khi đối chiếu ảnh nhãn, cần ánh xạ đối tượng tương ứng vì ID nhãn có thể bị hoán vị. Đây là thiết kế kiểm chứng đề xuất, chưa thực hiện.

## Thiết kế đánh giá đề xuất

Dataset nên gồm ảnh tổng hợp với ground truth từng đối tượng và ảnh thật có nhãn tham chiếu. Thử các mức nhiễu, mật độ, kích thước và mức độ chạm nhau. Tách tập chọn tham số và tập đánh giá cuối; không chọn tham số dựa trên điểm của tập đánh giá cuối.

Các phép đo phục vụ những câu hỏi khác nhau:

- IoU và Dice tiền cảnh: mask có khớp vùng đối tượng không?
- Precision, recall và F1 theo đối tượng sau ghép một đối một bằng IoU: tách đúng bao nhiêu đối tượng? Phải nêu ngưỡng IoU và cách tính TP, FP, FN.
- Sai số đếm tuyệt đối: chênh lệch số đối tượng so với ground truth.
- Số lỗi split và merge: một đối tượng bị chia hoặc nhiều đối tượng bị gộp.
- Thời gian: đo lặp, báo trung vị và độ phân tán; ghi cấu hình máy và tách đọc/ghi ảnh khỏi phần xử lý nếu đo tốc độ thuật toán.

IoU tiền cảnh cao vẫn có thể đi kèm lỗi gộp vật thể, nên cần phép đo theo đối tượng. Đối chiếu với Fiji là kiểm tra tính nhất quán triển khai; ground truth mới dùng để đánh giá độ đúng phân đoạn. Đề xuất ablation: bỏ xử lý hình thái, bỏ reconstruction hoặc thay cách tạo marker; so sánh chất lượng và thời gian trên cùng dữ liệu.

## Sản phẩm và phân công

Theo đề bài, cần báo cáo khoảng 30 trang và presentation khoảng 10 slides, có lý thuyết, code, minh họa Fiji và Python, số liệu định lượng và mã nhóm. Deadline được cung cấp là 19/11, chưa xác nhận năm hoặc giờ.

Phân công gợi ý của giảng viên: thành viên 1 phụ trách lý thuyết và mô hình; thành viên 2 cài đặt, tối ưu và kiểm thử; thành viên 3 khảo sát Fiji, workflow và macro; thành viên 4 dataset, ground truth, metric và biểu đồ. Chưa gán vai trò này cho từng người cụ thể.

Thứ tự triển khai đề xuất: xác định dữ liệu và thước đo; xây baseline nhỏ chạy được ở cả hai nền tảng; kiểm tra từng toán tử; mở rộng khảo sát và cải tiến; cuối cùng viết báo cáo và slides từ kết quả thực đo.
