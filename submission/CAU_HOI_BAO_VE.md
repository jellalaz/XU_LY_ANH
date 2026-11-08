# Câu hỏi luyện bảo vệ — đọc hiểu, không học thuộc máy móc

## 1. Đề tài nhóm làm gì?

Tách từng đối tượng trong ảnh bằng hình thái học và Watershed. Đầu ra là ảnh nhãn: nền bằng 0, mỗi vật thể một ID. Sau đó có thể đếm, đo diện tích và tâm. Không phải mô hình tự nhận biết tên người, xe hay con vật.

## 2. Có phải chỉ làm ứng dụng không?

Không. Phần chính là lý thuyết, tự cài thuật toán, chạy thí nghiệm, kiểm chứng bằng Fiji và đánh giá định lượng. CLI chạy được độc lập. App dùng cùng lõi và hỗ trợ chỉnh tham số, xem bước trung gian, demo thuận tiện.

## 3. Có train không? Tại sao vẫn có train/validation/test?

Không train trọng số. Đó là phân chia chính thức của BBBC039. Validation dùng khảo sát tham số; test dùng đánh giá cấu hình đã chọn. Tập training không được dùng huấn luyện trong bài này. Nếu chỉnh tiếp sau khi xem test, cần công khai và tìm tập độc lập mới để xác nhận.

## 4. Phần nào tự cài? Phần nào dùng thư viện?

Tự cài co/giãn/mở/đóng nhị phân bằng dịch SE, reconstruction bằng hàng đợi, CCL bằng BFS, khoảng cách Euclid bằng bao dưới parabola và Watershed bằng heap. Gaussian, Otsu, đọc ghi ảnh, chuẩn hóa và đo thuộc tính dùng thư viện. Có engine thư viện để đối chiếu, không gọi engine đó là code tự viết.

## 5. Khác nhau giữa opening và opening by reconstruction?

Opening thường co rồi giãn bằng cùng SE, có thể làm thay đổi biên/hình dạng. Opening by reconstruction co để tạo marker, rồi tái tạo dưới mask gốc; vùng còn seed có thể được khôi phục. Nó không tự tách được hai vật thể đang dính; cần bước tạo marker và Watershed.

## 6. Vì sao lấy âm của distance transform?

Khoảng cách tới nền lớn ở sâu trong đối tượng. Watershed lan từ vùng thấp; lấy E=−D biến tâm thành đáy. Nếu dùng distance dương, ý nghĩa địa hình đảo lại. Marker quyết định nơi bắt đầu lan nhãn, mask chặn nhãn lan ra nền.

## 7. Marker là gì, h tác động thế nào?

Marker là vùng hạt giống mang nhãn. Nhiều cực đại do nhiễu có thể tạo quá nhiều marker và chia thừa. H-maxima loại các cực đại nông; tăng h thường làm giảm marker nhưng có thể gộp vật thể thật. Một marker cho mỗi vật thể là mục tiêu, không phải bảo đảm tự động.

## 8. Liên thông 4 và 8 khác gì?

Liên thông 4 nối trên/dưới/trái/phải; liên thông 8 thêm các đường chéo. Ba pixel nằm chéo có thể là 3 vùng với liên thông 4 nhưng 1 vùng với liên thông 8. Phải thống nhất quy ước khi đối chiếu; thay liên thông có thể thay mask, marker và đường chia.

## 9. Fiji có phải nhãn đúng không?

Không. Fiji là nền tảng tham chiếu đã có triển khai chuẩn hóa. Hai chương trình giống nhau chưa chắc đúng vật thể thật. Ground truth là nhãn đối tượng dùng đánh giá. Fiji shared dùng chung đầu vào để kiểm chứng Watershed; Fiji native có tiền xử lý riêng nên trả lời câu hỏi khác.

## 10. Vì sao IoU cao mà F1 đối tượng thấp?

IoU tiền cảnh chỉ xem pixel thuộc vật hay nền. Hai vật thể gộp thành một vẫn có thể giữ mặt nạ tiền cảnh gần như hoàn hảo. F1 ghép một–một các vật thể với ngưỡng IoU≥0.5, nên phạt chia/gộp. Ví dụ ảnh mẫu: CCL cho 5 vùng, Watershed cho 7, nhưng cùng mask nên IoU tiền cảnh bằng nhau.

## 11. Vì sao Fiji native tốt hơn? Có chứng minh Watershed của Fiji hơn không?

Native đạt F1 khoảng 0.8917 trên 50 ảnh test trong đợt đo; Python custom khoảng 0.7087. Nhưng native dùng 8-bit, SE vuông, ImageJ EDM và extended maxima, khác toàn pipeline. Vì vậy chưa thể quy chênh lệch cho riêng Watershed. So sánh shared mới kiểm soát elevation/marker/mask để khảo sát riêng bước này.

## 12. Watershed có luôn tốt hơn CCL không?

Không. Trên 6 validation khảo sát, CCL đạt khoảng 0.8168 so với baseline hmax 0.6663. Marker chưa phù hợp có thể chia thừa những vật thể vốn đã tách. Vì vậy cần baseline, ablation và phân tích lỗi, không chỉ đưa ảnh demo đẹp.

## 13. Điểm cải tiến/tối ưu là gì? Có nhanh hơn không?

Có lọc cực đại bằng h-maxima, h thích nghi theo thành phần, reconstruction dùng hàng đợi để tránh quét lại toàn ảnh và EDT tuyến tính. Tuy nhiên ý tưởng ít thao tác chưa đồng nghĩa triển khai Python nhanh hơn thư viện biên dịch. Phép đo reconstruction bổ sung cho thấy queue Python chậm hơn vòng lặp dùng SciPy; báo cáo nêu rõ và chưa tuyên bố speedup.

## 14. Có đủ dữ liệu không? 200 là 200 thí nghiệm độc lập không?

BBBC039 có 200 ảnh với phân chia chính thức. Bảng chính dùng 50 ảnh test chạy 4 cách thành 200 dòng, không phải 200 ảnh test khác nhau. Ảnh có thể liên quan trong cùng thí nghiệm; biến đổi nhiễu/mờ từ một ảnh cũng không tạo mẫu độc lập. Khoảng tin cậy bootstrap theo ảnh chỉ phản ánh biến thiên trong tập khảo sát.

## 15. Khi demo sai hoặc đếm bằng 0 thì xử lý sao?

Xem lần lượt gray, binary, mask, distance, marker, labels. Nếu mask đã rỗng, không thể đổ lỗi Watershed. Ví dụ min_area=100000 lớn hơn toàn ảnh 192×192 nên tất cả bị loại; kết quả 0 là đúng theo cấu hình. Khôi phục cấu hình, chạy lại, ghi rõ thay đổi. Không chỉnh kết quả bằng tay rồi báo là thuật toán tự động.

## 16. Nhóm chứng minh khả năng tái lập thế nào?

Giữ code, cấu hình, seed ảnh tổng hợp, manifest và checksum dữ liệu, phiên bản thư viện/JAR, CSV từng ảnh và lệnh chạy. `academic_smoke.py` kiểm tra 7/5/0 vùng, Java/Python metric và Groovy replay. Bộ 29 test kiểm tra tính chất cụ thể. Thời gian vẫn phụ thuộc máy và tải hệ thống; kết quả chất lượng phải so cùng dữ liệu và quy ước.
