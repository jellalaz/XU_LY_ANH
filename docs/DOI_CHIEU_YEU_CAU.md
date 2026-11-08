# Đối chiếu yêu cầu bài tập lớn — Nhóm 1

Đề tài: **Phân đoạn đối tượng bằng hình thái học toán học và Watershed**, tham chiếu **MorphoLibJ trên Fiji/ImageJ**. Ứng dụng hỗ trợ thao tác và demo; không thay thế nghiên cứu, cài đặt và thực nghiệm. Thầy không yêu cầu bắt buộc một app tích hợp và không nêu điểm cộng riêng cho giao diện.

| Yêu cầu | Thành phần bàn giao | Minh chứng |
| --- | --- | --- |
| Lý thuyết rõ và sâu | Đủ 8 nội dung; công thức, ví dụ và độ phức tạp | Báo cáo; scripts/academic_checks.py |
| Khảo sát plugin Fiji | MorphoLibJ 1.6.5, shared và native, hướng dẫn thao tác | Ảnh native từng toán tử, file metric Java, phiên bản JAR |
| Cài đặt lại | Morphology dịch SE, deque reconstruction, EDT parabola, BFS CCL, heap Watershed | morpholab/algorithms.py; tests so SciPy/skimage |
| Python và Fiji thực chạy | Python CLI, Java adapter, script Groovy | scripts/academic_smoke.py; fiji/ReplayWatershed.groovy |
| Định lượng cả hai nền tảng | Python mask/instance/count; Java IoU, Dice, count độc lập | metrics.json; fiji_metrics.csv; comparison.json |
| Thực nghiệm và tối ưu | 50 test × 4 cách; ablation/robustness; khảo sát h; đo reconstruction 5 lần | docs/evidence/v2_*; docs/evidence/academic_checks |
| Báo cáo ~30 trang | Word/PDF với lý thuyết, code, hình, kết quả, giới hạn, tài liệu tham khảo | submission/BAO_CAO_NHOM_1.* |
| Presentation ~10 slide | 10 slide tổng cộng, biểu đồ/bảng sửa được, ghi chú có nguồn | submission/PRESENTATION_NHOM_1.pptx; THUYET_TRINH.md |
| Hướng dẫn chạy/test | Lệnh, kết quả kỳ vọng, thực hành Fiji, benchmark, xử lý lỗi | submission/HUONG_DAN_CHAY_VA_TEST.md |
| Một đại diện nộp LMS ghi mã nhóm | Hồ sơ ghi Nhóm 1 và 4 thành viên | Nhóm tự kiểm tra và nộp; chưa thao tác LMS |

## Phạm vi cần trình bày trung thực

- Không train mạng học sâu. 100/50/50 là phân chia BBBC039, không có nghĩa đã train trên 100 ảnh.
- Phần tự cài ở algorithms.py; Gaussian, Otsu, đọc/ghi và thống kê dùng thư viện.
- Fiji là tham chiếu, không phải ground truth. Native có tiền xử lý khác Python.
- CCL tốt hơn baseline hmax trên tập validation khảo sát; không khẳng định Watershed luôn tốt hơn.
- Queue Python chưa nhanh hơn lặp SciPy trong phép đo bổ sung; báo cáo giữ kết quả bất lợi này.
- Test phần mềm không chứng minh phân đoạn đúng mọi ảnh. F1=1 của demo không phải độ chính xác tổng thể.
- Nhóm cần đọc, chạy demo, giải thích được mã và sửa phân công theo đóng góp thực tế trước khi nộp. Không bảo đảm điểm số.
