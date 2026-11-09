# Sử dụng MorphoLab PTIT

Thực hành Fiji lần đầu: xem [hướng dẫn 6 bước](../submission/HUONG_DAN_FIJI_TUNG_BUOC.md). Báo cáo chính hiện là [PDF LaTeX](../submission/BAO_CAO_NHOM_1.pdf), có mục lục, hình và số trang tự động; nguồn trong `submission/latex`.

Ứng dụng hỗ trợ nghiên cứu phân đoạn từng đối tượng trong ảnh 2D bằng hình thái học và Watershed. Chạy `launch_app.cmd` để mở. Phần mềm sử dụng env `ai` hiện có; dữ liệu và kết quả nằm trong thư mục con của dự án.

## Thí nghiệm đầu tiên

1. Chọn **Ảnh mẫu có nhãn**. Đây là ảnh tổng hợp có ground truth hình học, dùng để kiểm tra thao tác.
2. Giữ `custom`, `hmax` và các tham số mặc định, rồi nhấn **Phân đoạn**.
3. Xem 6 bước. Combobox phía trên ảnh cho phép mở riêng erosion, dilation, reconstruction/morphology, components, elevation và các ảnh khác.
4. Nhấp một vật thể trên ảnh kết quả để xem diện tích, tâm và đường kính tương đương. Thanh công cụ Matplotlib hỗ trợ zoom/pan.
5. Tab **Fiji & đánh giá**: nhấn **Chạy Fiji / MorphoLibJ** để gọi chính plugin trên máy.
6. So sánh ba khung Python, Fiji và vùng khác sau ánh xạ ID. Có thể nạp kết quả TIFF đã xuất thủ công từ Fiji.
7. Nhấn **Xuất toàn bộ kết quả** và chọn thư mục cha. Mỗi lần xuất tạo thư mục riêng theo thời gian, tránh ghi đè lần trước.

## Giao diện và cảnh báo ở bản 1.2

Lựa chọn giữ tên thuật toán tiếng Anh, kèm giải thích trong ngoặc: `erosion (co ảnh)`, `dilation (giãn ảnh)`, `hmax (lọc cực đại theo h)`, `mask (vùng tiền cảnh)` và `ground truth (nhãn đúng)`. Di chuột trên các tham số chính để đọc gợi ý. Cấu hình JSON và tên trường CSV giữ nguyên để các lệnh cũ tiếp tục dùng được.

- Thanh thông báo dưới tên ảnh cho biết kết quả đã cũ khi bạn thay tham số. Chạy lại **Phân đoạn ảnh** trước khi so sánh Fiji, áp dụng marker hoặc xuất phiên.
- Nếu sửa marker, nhấn **Áp dụng marker** hoặc **Marker tự động** trước khi xuất và kiểm chứng.
- Nếu không còn đối tượng, ảnh kết quả hiện thông báo thay vì chỉ chồng ảnh gốc. Với ảnh 192×192, toàn ảnh chỉ có 36.864 pixel; đặt diện tích tối thiểu 100.000 sẽ loại hết vùng. Nhấn **Mặc định → Phân đoạn ảnh** để thử lại.
- F1 hiển thị `—` khi chưa có nhãn đúng; đây không phải điểm 0. IoU, Dice, F1 và PQ cao hơn thường tốt hơn; sai số đếm, Split (chia thừa) và Merge (gộp vật thể) thấp hơn tốt hơn.
- Zoom (phóng to) và Pan (di chuyển) được tô sáng khi bật. Bật sửa marker sẽ tắt chế độ này để thao tác chuột không bị lẫn. Vòng tròn trên ảnh marker giúp nhìn rõ vị trí khởi tạo, không làm thay đổi dữ liệu TIFF.

Phần mềm giúp chạy thí nghiệm và thu số liệu. Báo cáo khoảng 30 trang và slide khoảng 10 trang vẫn là sản phẩm chính cần biên soạn riêng; giao diện không thay thế nội dung nghiên cứu.

Ảnh thật: chọn **Bộ ảnh & nhãn**, chọn BBBC039 và split, bấm **Lọc danh sách**, nhấp đúp ảnh muốn mở. Ảnh và nhãn đúng được nạp cùng nhau. Với ảnh ngoài dataset, dùng **Chọn ảnh** và **Nạp ground truth**. Ground truth BBBC039 đã giải mã nằm trong `data/bbbc039/labels`.

## Làm việc trong một ứng dụng

Fiji không bị thay thế bằng code Python: ứng dụng gọi JAR MorphoLibJ thật qua Java, thu kết quả rồi hiển thị cùng Python. Bạn không phải mở cửa sổ Fiji để chạy kiểm chứng tự động. Khi cần minh họa trực tiếp nền tảng Fiji, mở Script Editor và chạy file Groovy đã xuất. Mỗi chức năng nghiên cứu còn có lệnh CLI tương ứng để tái lập.

**Sửa marker:** sau khi phân đoạn tự động, tích **Sửa marker**, nhấp trái trong vùng mask để thêm seed, nhấp phải để xóa vùng seed gần vị trí chọn nhất. Ảnh marker được hiển thị trên ảnh gốc. Nhấn **Áp dụng marker** để chạy lại Watershed; ảnh tự động và ảnh chỉnh thủ công phải được phân biệt khi báo cáo. Mỗi thành phần liên thông của mask cần ít nhất một marker. **Marker tự động** khôi phục cách tạo marker từ cấu hình đã chạy.

**Xem bảng đối tượng:** mở bảng thuộc tính có thanh cuộn, gồm ID, diện tích, tâm, bounding box, đường kính tương đương và đặc trưng hình dạng. Bảng CSV đầy đủ vẫn được xuất cùng phiên.

**Lưu và mở lại:** nút **Xuất toàn bộ kết quả** lưu phiên trong thư mục riêng, gồm ảnh đầu vào, ảnh trung gian, ground truth, nhãn Fiji nếu có, cấu hình và `report.html`. Tab **Phiên đã lưu** liệt kê các phiên và các study trong `outputs`; nhấp đúp để mở lại. Có thể mở phiên từ thư mục khác, nhưng thư mục lưu phiên mới phải trống. Không dùng pickle để tải dữ liệu.

**Nút Dừng tác vụ:** yêu cầu dừng hợp tác ở điểm kiểm tra; một số phép thư viện có thể cần hoàn thành lệnh hiện tại trước khi dừng. Đóng app trong lúc xử lý cũng gửi tín hiệu hủy và đợi worker thoát, bao gồm dừng và thu hồi tiến trình Fiji. JVM giới hạn heap 512 MB; tổng RAM gồm thêm thư viện và phần ngoài heap. Không mở nhiều phiên app để chạy benchmark cùng lúc nếu muốn số thời gian có ý nghĩa.

## Kế hoạch nghiên cứu tích hợp

Thiết lập dataset, split, số ảnh, số lần đo ở tab **Benchmark**, sau đó sang **Nghiên cứu**:

| Kế hoạch | Nội dung |
| --- | --- |
| `compare` | Chạy Python tự cài, thư viện, Fiji cùng đầu vào và workflow Fiji độc lập trên từng ảnh |
| `ablation` | Baseline, bỏ Gaussian, bỏ hình thái, thay reconstruction bằng opening thường, bỏ lấp lỗ, marker raw và CCL |
| `robustness` | Ảnh gốc, nhiễu Gaussian σ=0.02/0.05/0.1 và mờ σ=1/2/3, seed cố định |

Cấu hình `configs/research_library.json` dùng bản thư viện cho ablation/robustness nhanh hơn. Các biến thể hỏng ảnh dùng nhãn gốc để đo mức suy giảm; chúng có tương quan và không được tính như các mẫu test độc lập mới. Study không chọn tham số từ test; dùng validation cho khảo sát và cố định cấu hình trước khi đánh giá test.

Kết quả gồm `per_image.csv`, `summary.csv`, biểu đồ `quality.png`, `study.json` và phiếu `report.html`. F1 là macro mean, CI 95% là percentile bootstrap mô tả giữa các ảnh với 1000 lượt lấy mẫu. Một ảnh cho CI suy biến; CI không chứng minh chắc chắn một phương pháp vượt phương pháp khác. Khi một cấu hình lỗi, lỗi được ghi riêng, không biến thành điểm 0 hoặc tự động bỏ qua không thông báo. Khi hủy, phiếu kết quả chỉ gồm các lượt đã hoàn tất và trạng thái `cancelled`.

Thời gian được ghi riêng: pipeline Python không gồm IO/metric, Fiji shared chỉ đo Watershed, thời gian tiến trình Fiji gồm khởi động JVM, native pipeline gồm xuất ảnh trung gian. Kết quả chất lượng của native có tiền xử lý và marker khác Python nên không quy mọi chênh lệch cho riêng thuật toán Watershed.

Ví dụ đã hoàn thành nằm trong `outputs/v2_compare_bbbc039_test`, `outputs/v2_ablation_bbbc039`, `outputs/v2_robustness_bbbc039`; một phiên mẫu nằm trong `outputs/v2_example_session`. CSV và biểu đồ dùng cho báo cáo còn được giữ trong `docs/evidence`.

## Hai cách sử dụng Fiji

**Kiểm chứng Watershed trên cùng đầu vào:** Python cung cấp elevation float32, marker có nhãn, mask nhị phân và liên thông cho `Watershed.computeWatershed` của MorphoLibJ. Tắt dams ở cả hai bên. Đây là phép kiểm tra bước Watershed riêng, không chứng minh toàn bộ pipeline độc lập giống nhau. FIFO và cách xử lý plateau có thể tạo ranh giới khác.

**Workflow (quy trình) Fiji độc lập:** nhấn **Quy trình Fiji độc lập**. Fiji tự thực hiện lượng tử hóa 8-bit, Gaussian, Otsu, phần tử cấu trúc vuông, opening bằng reconstruction, fill holes, lọc diện tích, ImageJ EDM, extended maxima, gán nhãn và Watershed. Fiji lưu từng ảnh `native_*.tif` để minh họa. Đây là baseline cố định; nó sử dụng radius, sigma, h, min_area, polarity và connectivity hiện có, còn thao tác morphology/shape/mode/manual threshold/fill_holes của Python không được áp dụng cho baseline này. Quy ước cụ thể được ghi trong `native_parameters.txt`.

Cả hai cách đều sử dụng Java và JAR thực trong `C:/Tools/Fiji`. Chọn **Thư mục Fiji** nếu cài ở vị trí khác. Lần đầu chương trình biên dịch hai lớp adapter vào `build`; các lần sau tái sử dụng. Không sửa cài đặt Fiji hoặc env `ai`.

`fiji_metrics.csv` được Java/ImageJ tính độc lập IoU/Dice tiền cảnh và số đối tượng khi có ground truth. `comparison.json` bổ sung metric theo đối tượng bằng Python. `Run_in_Fiji.groovy` trong thư mục kết quả có thể mở bằng Fiji Script Editor, chọn Groovy, Run để xem lại bước Watershed bằng GUI Fiji. Với native workflow, script dùng các ảnh trung gian do Fiji đã tự tính.

Để tự khảo sát plugin bằng GUI Fiji: mở ảnh mask rồi dùng **Plugins → MorphoLibJ → Binary Images** cho distance map/connected components; **Filtering** cho morphology/reconstruction; **Minima and Maxima** cho cực trị; **Segmentation** cho Watershed. Tên lệnh cụ thể tùy phiên bản. Ghi lại hình dạng SE, radius, liên thông và tùy chọn dams khi minh họa.

## Ý nghĩa tham số

| Tham số | Ý nghĩa |
| --- | --- |
| engine | `custom`: thuật toán tự cài; `library`: bản thư viện đối chiếu |
| mode | `ccl`: vùng liên thông; `raw`: cực đại chưa lọc h; `hmax`: lọc cực đại theo h; `adaptive`: h theo thành phần |
| operation | Chọn xử lý mask, bao gồm opening, closing và opening bằng reconstruction |
| shape, radius | Phần tử cấu trúc disk/square/cross và bán kính tính bằng pixel |
| sigma | Mức làm trơn Gaussian trước ngưỡng |
| threshold | `-1`: Otsu; giá trị [0,1]: ngưỡng trên ảnh chuẩn hóa min–max |
| min_area | Loại thành phần có diện tích nhỏ hơn ngưỡng, đơn vị pixel² |
| connectivity | Lân cận 4 hoặc 8; dùng xuyên suốt pipeline Python |
| h | Độ nổi tối thiểu của cực đại trên distance map, đơn vị pixel khoảng cách |
| adaptive_fraction | `h_local=max(h, fraction × max_distance)` trong từng thành phần |
| fill_holes | Lấp các vùng nền kín bằng reconstruction |
| bright_foreground | Đối tượng sáng hay tối so với nền |

Sau khi sửa tham số, nhấn **Phân đoạn** để tính lại. File xuất lưu cấu hình đã thực sự chạy. Adaptive là hướng khảo sát, không có cam kết cải thiện; bộ thí nghiệm hiện có ghi nhận cả trường hợp không tốt hơn hmax.

## Ground truth và metric

Nhãn đầu vào phải là ảnh 2D số nguyên không âm: nền 0, mỗi vật thể có ID riêng. Kích thước phải trùng ảnh; chương trình không resize ground truth. Không dùng ảnh tô màu RGB thay cho ảnh nhãn. Nếu GT chỉ là mask tiền cảnh chung, IoU/Dice có ý nghĩa nhưng F1 theo từng vật thể không thể hiện đúng bài toán instance segmentation.

F1 ghép một–một các vùng có IoU ≥ 0.5: ưu tiên số cặp hợp lệ tối đa, rồi tổng IoU lớn nhất. Precision=TP/(TP+FP), recall=TP/(TP+FN), F1=2TP/(2TP+FP+FN). PQ dùng tổng IoU của các cặp hợp lệ chia TP+0.5FP+0.5FN. Hai ảnh rỗng có IoU/Dice/F1=1; chỉ một ảnh rỗng có F1=0.

Chẩn đoán split/merge đếm quan hệ giao có diện tích ≥10% diện tích vùng nhỏ hơn. Đây là quy ước phân tích của phần mềm, không phải định nghĩa duy nhất. So sánh ID nhãn với Fiji dùng ghép vùng tối đa số pixel giao nhau và chỉ tính độ đồng thuận trên hợp tiền cảnh để nền rộng không làm điểm số tăng giả.

## Xử lý hàng loạt và benchmark

Tab **Benchmark** hỗ trợ:

- **Xử lý thư mục ảnh**: chạy cấu hình hiện tại trên TIFF/PNG/JPG/BMP; bỏ qua file có hậu tố `_gt`. Tự ghép nhãn tùy chọn `tênảnh_gt.tif`, `.tiff` hoặc `.png`. Mỗi ảnh có thư mục xuất riêng, lỗi một ảnh được ghi vào `batch.csv` và các ảnh còn lại vẫn được xử lý.
- **Chạy 4 phương pháp × 2 bản**: so sánh ccl/raw/hmax/adaptive và custom/library trên dataset đã chọn. Có một lượt warm-up và số lần lặp do người dùng đặt; thời gian loại đọc/ghi và metric.
- **Khảo sát h trên validation**: h thuộc {0.5,1,2,4,6}, dùng bản cài đặt đang chọn và phương pháp hmax, chọn macro F1 cao nhất; lưu `selected_parameters.json` với đúng engine/hmax đã khảo sát. Nạp file đó để dùng. Chức năng này cố định validation, không dùng test để chọn tham số. Chọn library nếu muốn khảo sát nhanh hơn.

Không chạy benchmark lúc máy đang tải nặng nếu muốn đo thời gian dùng trong báo cáo. Chương trình ghi môi trường và thông số, nhưng không đo riêng mức sử dụng CPU/RAM. Thời gian pipeline CCL hiện vẫn bao gồm việc tạo ảnh distance/marker để phục vụ giao diện; vì vậy không coi đó là thời gian tối thiểu của riêng BFS.

Ví dụ CLI:

```bat
conda activate ai
cd /d D:\XU_LY_ANH
python -m morpholab batch data\synthetic --out outputs\batch
python -m morpholab sweep data\bbbc039\manifest.json --limit 6 --out outputs\sweep
python -m morpholab benchmark data\bbbc039\manifest.json --config outputs\sweep\selected_parameters.json --split test --engines library --repeats 2 --out outputs\test
python -m morpholab evaluate data\synthetic\synth_00_gt.tif outputs\demo\labels.tif
```

`per_image.csv` giữ kết quả từng ảnh; `summary.csv` là macro mean theo ảnh (riêng runtime là median các median). CSV đọc được bằng Excel. `benchmark.png` dùng trực tiếp cho báo cáo. Đây không phải chỉ số xếp hạng chính thức của bộ dữ liệu hoặc so sánh công bằng với bài báo dùng metric khác.

## Các tệp kết quả

`labels.tif` chứa ID số, `labels_rgb.png` chỉ để xem màu, `overlay.png` chồng kết quả lên ảnh gốc. `objects.csv` chứa diện tích, tâm, bounding box và đặc trưng hình dạng. `run.json` ghi tham số, threshold thực, thời gian từng bước, thư viện, hệ điều hành và SHA256 ảnh nguồn. Khi có ground truth, phần mềm ghi thêm `metrics.json`.

Các khoảng cách và diện tích hiện dùng pixel/pixel², chưa quy đổi sang micromet. Chưa hỗ trợ ảnh 3D hoặc xử lý video. Các file tải về, dữ liệu ảnh lớn và output không đưa lên Git; dùng lệnh dataset để chuẩn bị lại trên máy khác.
