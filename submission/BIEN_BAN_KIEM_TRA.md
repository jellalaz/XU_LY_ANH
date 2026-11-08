# Biên bản kiểm tra hồ sơ — 08/11/2026

Phạm vi: hoàn thiện phần học thuật của đề tài nhóm 1; giao diện hiện có là công cụ hỗ trợ, không phát triển thêm tính năng app trong đợt này.

## Kết quả đã kiểm tra

| Hạng mục | Kết quả | Minh chứng |
| --- | --- | --- |
| Bộ kiểm thử đầy đủ | 29/29 qua, bao gồm 7 luồng Tk và Fiji thật | `docs/evidence/academic_verification/unittest.txt` |
| Demo tự động | Hmax 7 vùng/F1=1; CCL 5/F1=0.8333; empty 0/F1=0 | `smoke_summary.json` cùng thư mục minh chứng |
| Java/Fiji tính metric | IoU/Dice/số lượng khớp với Python trên nhãn Fiji, cả shared và native | Assert trong `scripts/academic_smoke.py`; `smoke_summary.json` |
| Script Groovy | Chạy thật bằng Groovy/Fiji JAR với hiển thị tắt; ảnh nhãn giống hệt Java bridge | `groovy_replay_exact=true` trong summary |
| Benchmark CLI | 1 ảnh × 2 engine × 4 mode, 3 lần đo; tạo đủ 8 dòng tóm tắt | `benchmark_summary.csv` |
| Khảo sát h | 6 ảnh validation, 5 mức h, library/hmax | `sweep.csv` |
| CLI dữ liệu thật | 1 ảnh test qua 4 cách xử lý, không lỗi | `real_image_summary.csv` |
| Tính tay và reconstruction | Ma trận toán tử; đầu ra hai cách reconstruction bằng nhau; 3 kích thước × 2 cách × 5 lần | `docs/evidence/academic_checks` lưu phép đo dùng trong báo cáo |
| Báo cáo Word | 32 trang theo Word; có bảng, hình, công thức và code | `BAO_CAO_NHOM_1.docx` |
| Báo cáo PDF | 32 trang; văn bản tìm kiếm được; không còn chỉ thị dựng bảng; đã xem bản dựng các trang | `BAO_CAO_NHOM_1.pdf` |
| Presentation | 10 slide; 4 bảng và 2 biểu đồ native; 10 phần ghi chú; kiểm tra package/layout/import qua | `PRESENTATION_NHOM_1.pptx`; `presentation_validation.json` |

Số liệu nghiên cứu chính được giữ nguyên từ các đợt chạy đầy đủ: 200 dòng đối chiếu trên 50 test; 42 dòng ablation và 42 dòng robustness trên 6 validation. Đợt kiểm tra bàn giao chạy các ca nhỏ để xác nhận đường tái lập, không đổi nhãn tập test hoặc thay số liệu bằng kết quả demo.

## Các giới hạn được ghi nhận

- Test Tk ban đầu không khởi tạo được Tcl trong sandbox của công cụ. Chạy lại trên desktop thật với cùng env `ai` đã qua đủ 29 test; không cần sửa thuật toán hoặc cài lại env.
- Groovy đã được kiểm tra phần tính toán bằng headless binding. Hộp thoại chọn thư mục/hiển thị ảnh cần nhóm thao tác theo hướng dẫn khi luyện demo; không tuyên bố đã kiểm thử tự động mọi menu Fiji.
- Bộ xuất PDF trực tiếp của Word bị chờ. Các tiến trình Automation do tác vụ tạo đã được thu hồi. PDF cuối được dựng riêng từ nội dung DOCX bằng ReportLab, nhúng font tiếng Việt và kiểm tra lại 32 trang; có thể khác cách ngắt dòng so với Word.
- PPTX đã được render/kiểm tra cấu trúc, dữ liệu biểu đồ và khả năng nhập lại bằng công cụ tạo slide. Chưa kiểm tra sửa biểu đồ rồi lưu/mở lại trong PowerPoint hoặc Google Slides; nhóm nên mở trên máy trình chiếu trước buổi bảo vệ.
- Báo cáo có kết quả bất lợi: CCL tốt hơn baseline trên tập validation khảo sát; queue Python chậm hơn SciPy trong phép đo reconstruction. Không sửa số liệu để tạo kết luận cải tiến thành công.
- Chưa nộp LMS. Nhóm cần xác nhận phân công thực tế, đọc hiểu nội dung và kiểm tra hạn nộp trong LMS.

## Tệp tạo lại tài liệu

- `scripts/build_report.py`: dựng DOCX từ `submission/report_source.md` và số liệu gốc.
- `scripts/build_report_pdf.py`: dựng PDF từ DOCX bằng python-docx/ReportLab và font Windows.
- `scripts/build_slides.mjs`: dựng slide và kiểm tra dữ liệu biểu đồ bằng runtime artifact-tool đã dùng khi biên soạn. Đường dẫn runtime hiện gắn với máy này; không cần script này để mở PPTX hoặc chạy thí nghiệm.
- `scripts/render_word_metafiles.ps1`, `render_report_pages.py`: công cụ kiểm tra bố cục, không thuộc thuật toán xử lý ảnh.

Chạy nghiên cứu chỉ cần env `ai` và Fiji theo hướng dẫn; các thư viện dựng tài liệu không phải phụ thuộc của phần mềm phân đoạn.
