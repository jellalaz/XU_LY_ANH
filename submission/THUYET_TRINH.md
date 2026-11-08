## Slide 1

40 giây. Giới thiệu đề tài nhóm 1. Mục tiêu: hiểu và tự cài đặt các phép hình thái, tạo marker và tách từng vật thể, rồi kiểm chứng bằng Fiji/MorphoLibJ. Đây là xử lý ảnh cổ điển, không huấn luyện mạng học sâu. Ứng dụng chỉ hỗ trợ thao tác; bằng chứng chính là mã nguồn, dữ liệu và báo cáo. Nguồn yêu cầu: đề bài và ảnh phân nhóm do người học cung cấp.

## Slide 2

50 giây. synth_00 có 7 vật thể, gồm 2 cặp chạm nhau. Connected components cho 5 vùng; Watershed với marker phù hợp cho 7. Mỗi đối tượng nhận một ID; có thể đếm và đo diện tích, tâm. Không tự nhận biết tên người, xe hay loại tế bào. Nguồn: outputs/input_output_example; data/synthetic/synth_00.tif và synth_00_gt.tif. Fiji trong hình là kết quả MorphoLibJ thực chạy. F1=1 trên ví dụ không chứng minh mọi ảnh đều tốt.

## Slide 3

70 giây. Giải thích phần tử cấu trúc B; nền ngoài ảnh bằng 0. Erosion: co. Dilation: giãn. Opening = co rồi giãn; closing = giãn rồi co. Reconstruction giãn marker nhưng bị chặn bởi mask đến hội tụ. Opening by reconstruction khôi phục vùng còn seed. Connected components gán ID các vùng nối nhau theo 4/8 lân cận. Mã tự viết: morpholab/algorithms.py. Nguồn: MorphoLibJ manual v1.6.5, https://imagej.net/plugins/morpholibj ; tài liệu PTIT tại materials/downloads/ptit_morphology.pdf.

## Slide 4

70 giây. Distance transform: khoảng cách Euclid tới nền. Tâm vùng thường có giá trị lớn. E=-D biến tâm thành đáy vùng. H-maxima dùng reconstruction loại cực đại nông, tránh thừa marker. Watershed lan nhãn bằng heap theo cost(q)=max(cost(p),E(q)). Bản tự cài không tạo dams; xử lý hòa bằng thứ tự vào hàng. Fiji có thể khác ở plateau. EDT dùng bao dưới parabola tuyến tính theo số pixel. Nguồn: algorithms.py; https://cs.brown.edu/people/pfelzens/dt/index.html ; https://imagej.net/plugins/morpholibj.

## Slide 5

70 giây. Shared dùng cùng elevation, markers, mask và liên thông: so sánh bước Watershed. Native chạy Fiji từ ảnh xám: Gaussian, Otsu, hình thái, EDM, extended maxima, Watershed. Native lượng tử 8-bit và SE vuông; Python mặc định float và SE đĩa. Không quy chênh lệch F1 về riêng Watershed. Java adapter gọi JAR thật. Fiji tự tính IoU, Dice và số vùng trong fiji_metrics.csv. Script Groovy chạy lại bằng Script Editor. Nguồn fiji/MorphoBridge.java, NativePipeline.java, ReplayWatershed.groovy và MorphoLibJ manual.

## Slide 6

65 giây. 18 ảnh tổng hợp có GT: 6 validation, 12 test. BBBC039: 200 ảnh nhân tế bào U2OS, chia chính thức 100 training, 50 validation, 50 test. Không train mô hình. Khảo sát 6 validation; bảng chính 50 test × 4 cách =200 dòng. F1 ghép một-một IoU>=0.5, trung bình theo ảnh. IoU/Dice tiền cảnh không đủ nhận diện lỗi chia/gộp. Nguồn https://bbbc.broadinstitute.org/BBBC039 ; manifest, metrics.py, studies.py.

## Slide 7

75 giây. F1 theo ảnh: custom0.7086889, library0.7053689, shared0.7188375, native0.8917349. CI95 bootstrap1000 lần theo ảnh: [.6807,.7305], [.6771,.7277], [.6914,.7386], [.8592,.9132]. Ba cách đầu cùng mask nên IoU tiền cảnh=.8954, native=.8910. Mặt nạ tốt chưa đủ tách đúng từng vật. Khác biệt toàn pipeline, chưa chứng minh một kernel luôn tốt hơn. Nguồn docs/evidence/v2_compare_bbbc039_test/summary.csv và per_image.csv.

## Slide 8

70 giây. Trên 6 validation: baselineF1=.6663, bỏ Gaussian=.6884, rawmarkers=.1563, CCL=.8168. Đây là4/7 biến thể; bảng đầy đủ trong báo cáo. CCL tốt hơn cho thấy baseline còn chia thừa. Blur sigma3 làmF1xuống.6018. Không khẳng định mọi bước hình thái đều cải thiện. Nguồn docs/evidence/v2_ablation_bbbc039/summary.csv và v2_robustness_bbbc039/summary.csv. Các biến đổi cùng ảnh không là mẫu độc lập.

## Slide 9

70 giây. Bộ unittest29 trường hợp có kiểm chứng Fiji thật, metric, GUI. Reconstruction5 lần sauwarmup1; mask1,seedtâm, liên thông4; mỗi cặp kết quả bằng nhau. QueuePython chậm hơn synchronousSciPy biên dịch. Đây là so sánh triển khai, không tách riêng độ phức tạp. Không so nativeIOtime trực tiếp với kernelPython. Nguồn docs/evidence/academic_checks/timing_summary.csv, protocol.json ; scripts/academic_checks.py ; tests.

## Slide 10

60 giây. Đóng góp: lý thuyết8 nội dung; tự cài thuật toán; workflowFiji thật; dữ liệu và định lượng; báo cáo và10slide. Demo academic_smoke tạo3casePython vàshared/nativeFiji, mởlabelsCSV. Giới hạn: nền phức tạp, marker nhạy, tốc độPython, không nhận dạng ngữ nghĩa. Có thể cải thiệnmarker và vònglặp, nhưng cần validation độc lập. GUI chỉ hỗ trợ. Nguồn đầy đủ trong báo cáo và https://github.com/jellalaz/XU_LY_ANH.
