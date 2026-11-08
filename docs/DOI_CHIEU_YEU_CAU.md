# Đối chiếu phần mềm với yêu cầu bài tập lớn

| Yêu cầu | Thành phần đáp ứng | Minh chứng |
| --- | --- | --- |
| Lý thuyết thuật toán rõ và sâu | `algorithms.py` có quy ước, công thức và cài đặt; tab Thuật toán; ghi chú nghiên cứu | Có thể chỉ ra từng phép toán và ảnh trung gian; phần báo cáo lý thuyết hoàn chỉnh vẫn cần biên soạn |
| Tham khảo plugin Fiji/ImageJ | MorphoLibJ thực; hai giao thức gọi Java; Script Editor Groovy | Ảnh native từng toán tử, file metric do Java tính, phiên bản JAR |
| Cài đặt lại thuật toán | Binary morphology bằng dịch SE; reconstruction hàng đợi; EDT tách trục; BFS CCL; priority flood Watershed | `morpholab/algorithms.py`; test với SciPy/scikit-image |
| Thực nghiệm và định lượng | Ground truth, metric mask/instance/count, benchmark, khảo sát tham số | CSV từng ảnh, summary, biểu đồ, môi trường và cấu hình |
| Python đối chiếu Fiji | Chung elevation/marker/mask, hoặc workflow Fiji độc lập | TIFF nhãn, bản đồ khác biệt, comparison JSON; không yêu cầu ID số giống nhau |
| Khảo sát cải tiến và tối ưu | Raw/hmax/adaptive, tự cài so với thư viện tối ưu, nhiều mức h | Có số liệu thực và giới hạn; không gọi một phương pháp là cải tiến thành công nếu kết quả không ủng hộ |
| Báo cáo ~30 trang, slides ~10 trang | Dữ liệu, hình, bảng và mô tả để biên soạn | Chưa tạo bản báo cáo/slides hoàn chỉnh hoặc nộp LMS |

Giao diện là phần bổ sung để sử dụng và trình diễn. Phần nghiên cứu có thể chạy độc lập qua CLI với cùng phần lõi. Chương trình hỗ trợ các yêu cầu kỹ thuật của đề tài; chất lượng báo cáo, phân tích, lựa chọn thí nghiệm và phần bảo vệ vẫn là các phần riêng cần hoàn thiện.

Phiên bản 1.1 bổ sung kế hoạch nghiên cứu tích hợp, kiểm chứng cả bốn cách chạy trên toàn bộ 50 ảnh test, phân tích ablation/robustness, sửa marker, lưu/mở lại phiên và phiếu HTML. Thầy không yêu cầu một app duy nhất; thiết kế hợp nhất này phục vụ thao tác và demo, đồng thời giữ code CLI và script Fiji để giải thích và kiểm chứng độc lập.
