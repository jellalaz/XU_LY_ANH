# Hướng dẫn chạy, kiểm chứng và bảo vệ — PTIT nhóm 1

**Mới học Fiji:** mở [Thực hành Fiji lần đầu — 6 bước](HUONG_DAN_FIJI_TUNG_BUOC.md). Báo cáo chính đã chuyển sang PDF biên dịch LaTeX; phần thực hành nằm ở Chương 4, phần app ở Chương 6. Word là bản trước khi bổ sung LaTeX.

Đề tài: **Phân đoạn đối tượng bằng hình thái học toán học và Watershed**. Dùng Python để tự cài và thực nghiệm; dùng **Fiji/ImageJ + MorphoLibJ** làm nền tảng tham chiếu. Không có bước huấn luyện mô hình AI. Không cần mở ứng dụng MorphoLab để chạy phần nghiên cứu.

## 1. Mở đúng môi trường

Mở Start → tìm **Anaconda Prompt / Miniconda Prompt**. Chạy từng dòng:

```bat
conda activate ai
cd /d D:\XU_LY_ANH
python --version
python -c "import numpy,scipy,skimage,tifffile; print('Thu vien Python: OK')"
python -c "from morpholab.fiji import installation; print(*installation(),sep='\n')"
```

Lệnh cuối phải in được bốn đường dẫn Java, javac, ImageJ JAR và MorphoLibJ JAR ở `C:\Tools\Fiji`. Trên máy hiện tại, env `ai` và Fiji đã được cài. Không cần cài lại khi các lệnh kiểm tra thành công. Nếu dùng **PowerShell**, đổi dòng chuyển thư mục thành `Set-Location D:\XU_LY_ANH`; các lệnh `python ...` vẫn giống nhau. Các lệnh `set ...` phía dưới dành cho Anaconda Prompt, không phải PowerShell.

Nếu clone trên máy mới, cài phụ thuộc theo `requirements.txt`, đặt Fiji trong `C:\Tools\Fiji`, bật IJPB-plugins qua Help → Update → Manage update sites, Apply Changes rồi mở lại Fiji. `requirements-lock.txt` ghi phiên bản đã đo; không khẳng định máy khác có cùng thời gian chạy.

## 2. Chạy demo có kiểm tra tự động — nên làm bước này trước

```bat
python scripts/academic_smoke.py
```

Script tạo thư mục mới dạng `outputs\academic_smoke_YYYYMMDD_HHMMSS`, không mở app và không ghi đè các đợt cũ. Nếu ảnh tổng hợp chưa có, nó tạo dữ liệu trước. Chờ đến dòng **ALL CHECKS PASSED** và đường dẫn kết quả. Lệnh kết thúc sẽ trả lại dấu nhắc `(ai)`; không để server chạy ngầm.

| Dòng PASS | Kết quả cần thấy | Ý nghĩa |
| --- | --- | --- |
| `hmax` | 7 objects; F1=1.0000 | Tách được hai cặp vật thể đang chạm nhau |
| `ccl` | 5 objects; F1=0.8333 | Chỉ gán nhãn liên thông, hai cặp chạm bị gộp |
| `empty` | 0 objects; F1=0.0000 | Diện tích tối thiểu 100000 loại hết vùng trong ảnh 192×192 |
| `fiji_shared` | 7 objects; F1=1.0000; metrics agree | Fiji thực chạy Watershed trên cùng dữ liệu |
| `fiji_native` | 7 objects; F1=1.0000; metrics agree | Fiji tự tính cả quy trình tham chiếu |
| `Groovy replay` | same labels as Java bridge | Script Groovy thật cho đúng ảnh nhãn của Java bridge |

`F1=1` chỉ đúng cho ví dụ này. Không hiểu thành chính xác 100% trên mọi ảnh. Thời gian thay đổi theo máy; không lấy một giá trị thời gian cố định làm điều kiện pass.

Mở thư mục kết quả vừa được in. Vào `hmax`, mở `overlay.png` hoặc `labels_rgb.png`: phải thấy 7 vùng màu. Mở `objects.csv`: có 7 dòng đối tượng ngoài dòng tiêu đề. Mở `metrics.json`: xem `true_objects`, `predicted_objects`, `object_f1`. So sánh với hai thư mục `ccl` và `empty`.

## 3. Chạy từng bước bằng lệnh để hiểu dữ liệu

Các lệnh sau dùng tên thư mục cố định để dễ trình diễn; chạy lại sẽ thay kết quả trong chính thư mục đó. Đổi tên `demo_shared` khi muốn giữ một đợt cũ.

```bat
python -m morpholab dataset synthetic
python -m morpholab segment data\synthetic\synth_00.tif --truth data\synthetic\synth_00_gt.tif --config configs\default.json --out outputs\demo_shared --fiji
```

Input là `synth_00.tif`; ground truth (nhãn đúng) là `synth_00_gt.tif`. Ground truth chỉ dùng chấm kết quả, **không được đưa vào thuật toán để tạo dự đoán**.

| Tệp trong `outputs/demo_shared` | Mở để kiểm tra gì? |
| --- | --- |
| `gray.tif`, `smoothed.tif` | Ảnh xám chuẩn hóa và ảnh làm trơn Gaussian |
| `binary.tif` | Tiền cảnh sau phân ngưỡng |
| `erosion.tif`, `dilation.tif` | Minh họa phép co và giãn |
| `morphology.tif`, `mask.tif` | Kết quả hình thái và mặt nạ sau lọc vùng/lấp lỗ |
| `components.tif` | Nhãn các vùng liên thông trước tách |
| `distance.tif`, `elevation.tif` | Khoảng cách tới nền và địa hình −distance |
| `markers.tif` | Nhãn các hạt giống khởi tạo |
| `labels.tif` | Nhãn dự đoán cuối cùng; nền 0, mỗi vật thể một số nguyên |
| `overlay.png`, `labels_rgb.png` | Ảnh màu để minh họa, không dùng thay TIFF nhãn khi chấm |
| `objects.csv` | Diện tích, tâm, hộp bao và thuộc tính từng vùng |
| `metrics.json` | Điểm Python so với ground truth |
| `run.json` | Cấu hình, thời gian, phiên bản môi trường và SHA256 ảnh nguồn |

Kỳ vọng mặc định: 7 vật thể, F1=1; IoU tiền cảnh xấp xỉ 0.981397; Dice xấp xỉ 0.990611. IoU thấp hơn 1 vì biên sau làm trơn/ngưỡng không trùng hoàn toàn nhãn đúng.

## 4. Kiểm chứng Fiji, không chỉ nhìn ảnh Python

Trong `outputs/demo_shared/fiji`:

- `morpholibj_labels.tif`: ảnh nhãn do MorphoLibJ thật tạo ra.
- `fiji_metrics.csv`: số lượng, IoU và Dice được **Java/ImageJ tính độc lập**.
- `comparison.json`: đánh giá Fiji với nhãn đúng và mức đồng thuận Python–Fiji.
- `disagreement.tif`: các pixel nhãn không đồng thuận sau ghép ID.
- `Run_in_Fiji.groovy`: script có sẵn đường dẫn để chạy lại trong Fiji.
- `bridge.log`: nhật ký lệnh Java; dùng khi cần tìm lỗi.

Mở `metrics.json` bên Python và `fiji_metrics.csv`. Ở ví dụ mặc định, IoU/Dice của hai bên trùng vì cùng mặt nạ; ranh giới giữa các nhãn có thể khác. Độ đồng thuận giữa hai chương trình không thay thế độ đúng với ground truth.

### 4.1. Chạy trực tiếp bằng Fiji Script Editor

1. Mở `C:\Tools\Fiji\fiji-windows-x64.exe`.
2. Chọn **File → Open**, mở `D:\XU_LY_ANH\outputs\demo_shared\fiji\Run_in_Fiji.groovy`.
3. Nếu xuất hiện Script Editor, đặt **Language → Groovy**, bấm **Run**. Nếu tệp không mở bằng editor, dùng **File → New → Script**, dán nội dung script vào rồi chọn Groovy.
4. Cửa sổ nhãn kết quả xuất hiện; tệp `fiji_interactive_labels.tif` được lưu trong cùng thư mục.
5. Ảnh nhãn nhìn gần như đen có thể do thang hiển thị nhỏ. Dùng **Image → Lookup Tables** chọn bảng màu hoặc chỉnh Brightness/Contrast để xem. Giữ dữ liệu nhãn TIFF gốc, không chuyển thành RGB rồi dùng chấm.
6. Quay lại Anaconda Prompt:

```bat
python -m morpholab evaluate data\synthetic\synth_00_gt.tif outputs\demo_shared\fiji\fiji_interactive_labels.tif --out outputs\demo_shared\fiji\interactive_metrics.json
```

Kỳ vọng 7 vật thể, F1=1. Đây là một chu trình có đủ **Python → dữ liệu kiểm chứng → Fiji → TIFF → đánh giá**.

Có thêm script dùng chung `fiji/ReplayWatershed.groovy`: mở bằng Script Editor, chọn Groovy, Run; chọn thư mục `outputs/demo_shared/fiji`, liên thông 4, bật hiển thị ảnh. Script này không chứa đường dẫn cố định. `academic_smoke.py` đã kiểm tra chính phần xử lý Groovy này ở chế độ không hiện cửa sổ. Việc chọn hộp thoại bằng tay là bước bạn thực hành khi demo.

### 4.2. Thao tác bằng menu MorphoLibJ

1. Mở ba ảnh `elevation.tif`, `markers.tif`, `mask.tif` trong thư mục Fiji nói trên.
2. Vào **Plugins → MorphoLibJ → Segmentation → Marker-controlled Watershed**. Nếu tên lệnh hơi khác ở phiên bản khác, gõ `Marker-controlled Watershed` vào ô tìm lệnh Fiji.
3. Chọn Input = elevation, Marker = markers, Mask = mask; Compactness = 0. Trên MorphoLibJ 1.6.5, bỏ **Use diagonal connectivity** để dùng liên thông 4; bỏ **Binary markers** vì marker đã mang ID; bỏ **Calculate dams** để không tạo đường phân cách nền. Nếu phiên bản khác có danh sách Connectivity, chọn 4.
4. Chạy; lưu kết quả ở một tên TIFF mới, sau đó dùng lệnh `evaluate` tương tự.

Giữ nguyên dấu âm của elevation. Distance dương có đỉnh tại tâm; dùng −distance để tâm là đáy vùng ngập. Không thay liên thông hoặc làm tròn ảnh giữa hai lần đối chiếu rồi đòi kết quả giống nhau.

### 4.3. Quy trình Fiji độc lập

```bat
python -m morpholab segment data\synthetic\synth_00.tif --truth data\synthetic\synth_00_gt.tif --out outputs\demo_native --fiji-native
```

Mở các tệp `native_*.tif` và `native_parameters.txt` trong `outputs/demo_native/fiji`. Fiji tự tính Gaussian, Otsu, co/giãn/mở/đóng, opening by reconstruction, lấp lỗ, lọc diện tích, ImageJ EDM, extended maxima, gán nhãn và Watershed.

Native là baseline cố định: 8-bit, SE vuông, Otsu, opening reconstruction. Các tùy chọn Python `operation`, `shape`, `mode`, ngưỡng thủ công, `fill_holes` và marker thủ công không được native chuyển thành cùng thao tác. Vì vậy đây là đối chiếu **toàn quy trình**, không phải thí nghiệm chỉ đổi riêng Watershed. Native có ghi ảnh trung gian; không lấy thời gian này chia thẳng cho thời gian kernel Python để kết luận nhanh hơn bao nhiêu.

## 5. Đọc mã để trình bày phần tự cài

Mở thư mục dự án bằng VS Code hoặc trình soạn thảo bạn dùng. Không bắt buộc chạy app.

| Tệp | Nội dung cần hiểu |
| --- | --- |
| `morpholab/algorithms.py` | Dịch phần tử cấu trúc để co/giãn; reconstruction bằng deque; EDT bằng bao dưới parabola; BFS CCL; heap Watershed |
| `morpholab/pipeline.py` | Ghép các bước và chọn bản tự cài/bản thư viện |
| `morpholab/metrics.py` | Ghép một–một nhãn; IoU, Dice, F1, PQ, split/merge |
| `morpholab/benchmark.py`, `studies.py` | Đo lặp, khảo sát tham số, kế hoạch so sánh, ablation và stress test |
| `fiji/NativePipeline.java`, `MorphoBridge.java` | Gọi API ImageJ/MorphoLibJ thật, xuất nhãn và metric phía Java |
| `fiji/ReplayWatershed.groovy` | Chạy lại bước Watershed trong Fiji |

Gaussian, Otsu, đọc/ghi ảnh, thống kê và chuẩn hóa dùng thư viện; không nhận là toàn bộ chương trình viết từ đầu. Phần thuật toán tự viết được chỉ rõ trong báo cáo và mã nguồn.

## 6. Chạy bộ kiểm thử

```bat
python -B -m unittest discover -s tests -v
```

Mặc định phát hiện 29 trường hợp, chạy 22 và bỏ qua 7 test giao diện; thông báo `OK (skipped=7)` là đúng. Bộ này có test toán tử, trường hợp biên, metric, hủy tác vụ, lưu phiên và Fiji thật. Khi muốn chạy cả test cửa sổ Tk, trong Anaconda Prompt:

```bat
set MORPHOLAB_DESKTOP_TEST=1
python -B -m unittest discover -s tests -v
set MORPHOLAB_DESKTOP_TEST=
```

Các cửa sổ kiểm thử có thể xuất hiện rồi tự đóng. Kỳ vọng `Ran 29 tests` và `OK`, không lỗi, không skipped. Trên PowerShell đặt `$env:MORPHOLAB_DESKTOP_TEST='1'`, chạy test rồi `Remove-Item Env:MORPHOLAB_DESKTOP_TEST`.

Kiểm thử chỉ xác nhận các tính chất và trường hợp đã viết, không chứng minh phân đoạn đúng trên mọi ảnh. Ảnh thật được đánh giá riêng bằng ground truth.

### Ví dụ tính tay và thực nghiệm reconstruction

```bat
python scripts/academic_checks.py --out outputs\academic_checks_new
```

Xem `hand_examples.json`: khối 3×3 trong ảnh 7×7 cho diện tích A=9, erosion=1, dilation=25; opening/closing khôi phục khối ở giữa. Xem đường chéo 3 pixel: liên thông 4 có 3 vùng, liên thông 8 có 1 vùng. `timing.csv` lưu mỗi lần đo; `timing_summary.csv` lưu trung vị/min/max. Đo 5 lần sau 1 warm-up và kiểm tra đầu ra reconstruction bằng nhau. Kết quả đo gốc trong `docs/evidence/academic_checks` cho thấy queue Python chậm hơn vòng lặp gọi SciPy biên dịch; không tuyên bố tối ưu thành công khi chưa có số liệu ủng hộ.

## 7. Benchmark và khảo sát tham số

Chạy nhỏ trước:

```bat
python -m morpholab benchmark data\synthetic\manifest.json --split validation --limit 1 --repeats 3 --out outputs\benchmark_small
python -m morpholab sweep data\synthetic\manifest.json --limit 6 --config configs\research_library.json --out outputs\sweep_small
```

Benchmark mặc định so sánh 2 engine × 4 phương pháp = 8 dòng tóm tắt khi chỉ dùng 1 ảnh. Mỗi phép đo có warm-up, dùng trung vị các lần lặp. Cùng ảnh/cấu hình vẫn có thể khác thời gian theo tải máy. Sweep khảo sát h trên **validation**, xuất bảng và cấu hình chọn; không tối ưu tham số bằng nhãn test rồi gọi test là đánh giá độc lập.

Đọc tên tệp CSV/PNG được tạo trong thư mục đích. `summary.csv` là bảng tổng hợp; `per_image.csv` (study) hoặc bảng benchmark từng ảnh cho phép kiểm tra từng trường hợp. Không xóa dòng lỗi để làm bảng đẹp; khi có lỗi phải đọc thông báo và xử lý trước khi kết luận.

## 8. Dữ liệu thật BBBC039 và các đợt nghiên cứu

Máy hiện tại đã có 200 ảnh trong `data/bbbc039`. Khi clone mới chưa có dữ liệu:

```bat
python -m morpholab dataset bbbc039
```

Ảnh tải trong thư mục con `data/raw`; ảnh và nhãn xử lý trong `data/bbbc039`. Tài liệu tải về nằm trong `materials/downloads`. Các tệp dung lượng lớn này được Git bỏ qua. Nguồn: https://bbbc.broadinstitute.org/BBBC039 (CC0). Dữ liệu được giữ phân chia chính thức 100 training / 50 validation / 50 test. Không có bước train; tập training không dùng cập nhật trọng số.

Chạy nhỏ 1 ảnh test để biết mọi phụ thuộc hoạt động:

```bat
python -m morpholab study data\bbbc039\manifest.json --kind compare --split test --limit 1 --repeats 1 --out outputs\compare_one
```

Kỳ vọng 4 dòng `status=ok`, tương ứng Python custom, Python library, Fiji shared, Fiji native. Điểm ảnh thật không được yêu cầu bằng 1.

Chạy lại đúng quy mô bảng đã nộp, chọn **tên thư mục mới** mỗi đợt:

```bat
python -m morpholab study data\bbbc039\manifest.json --kind compare --split test --limit 50 --repeats 1 --out outputs\compare_50_new
python -m morpholab study data\bbbc039\manifest.json --config configs\research_library.json --kind ablation --split validation --limit 6 --repeats 1 --out outputs\ablation_6_new
python -m morpholab study data\bbbc039\manifest.json --config configs\research_library.json --kind robustness --split validation --limit 6 --repeats 1 --out outputs\robustness_6_new
```

Đối chiếu: 200 dòng; ablation: 42 dòng; robustness: 42 dòng. Xem `per_image.csv`, `summary.csv`, `study.json`, hình `quality.png` và phiếu HTML trong mỗi thư mục. Chạy `python -m morpholab report outputs\compare_50_new` để tạo lại phiếu nghiên cứu. Với nghiên cứu hiệu năng nghiêm túc hơn, tăng `--repeats 3` và ghi rõ đó là đợt đo mới; bảng đã nộp dùng 1 lần đo sau warm-up.

Số liệu gốc đã lưu, không bắt buộc chạy lại toàn bộ trước khi xem báo cáo:

| Thư mục | Số ảnh/cấu hình | F1 trung bình theo ảnh |
| --- | --- | --- |
| `docs/evidence/v2_compare_bbbc039_test` | 50 test × 4 cách | Custom 0.7087; library 0.7054; shared 0.7188; native 0.8917 |
| `docs/evidence/v2_ablation_bbbc039` | 6 validation × 7 | Baseline 0.6663; raw markers 0.1563; CCL 0.8168 |
| `docs/evidence/v2_robustness_bbbc039` | 6 validation × 7 | Clean 0.6663; blur σ=3: 0.6018 |

Không kết luận Watershed luôn tốt hơn CCL: chính số liệu này cho thấy CCL tốt hơn baseline trên 6 ảnh validation. Đây là điểm cần giải thích về tạo marker và chia thừa, không phải số liệu cần giấu.

## 9. Thử ảnh của bạn và chạy hàng loạt

```bat
python -m morpholab segment "D:\duong_dan\anh_cua_ban.png" --out outputs\anh_cua_ban
python -m morpholab batch "D:\thu_muc_anh" --out outputs\batch_new
```

Thay đường dẫn ví dụ bằng tệp/thư mục thật. Chấp nhận ảnh 2D hoặc RGB/RGBA; RGB được đổi xám. Với nhãn đúng, thêm `--truth "D:\duong_dan\nhan.tif"`. Trong batch, đặt nhãn `tenanh_gt.tif` cạnh `tenanh.png`/`tenanh.tif`. Thư mục output phải khác thư mục input.

Không có nhãn đúng thì vẫn phân đoạn/đếm/đo được, nhưng **không có căn cứ tính F1 so với vật thể thật**. Ảnh tự nhiên nền rối, bóng đổ, đối tượng nhiều màu có thể không phù hợp cách ngưỡng toàn cục. Không nhầm số vùng tìm được với số vật thể chắc chắn đúng.

## 10. Lỗi thường gặp

| Hiện tượng | Kiểm tra và xử lý |
| --- | --- |
| `No module named morpholab` | Chuyển về `D:\XU_LY_ANH`; kích hoạt env ai |
| Thiếu `skimage`, `scipy`… | Kiểm tra `where python`; đúng env thì `python -m pip install -r requirements.txt` |
| Không tìm thấy Java/JDK/MorphoLibJ | Kiểm tra đường dẫn Fiji; cài IJPB-plugins rồi restart; dùng `--fiji-home` nếu lưu chỗ khác |
| Script Groovy không chạy | Chọn Language=Groovy; chọn đúng thư mục có đủ elevation, markers, mask |
| Ảnh nhãn đen | Xem LUT/contrast; nhãn 1…7 không phải RGB; không sửa dữ liệu để chấm |
| Đếm bằng 0 | Kiểm tra mask, ngưỡng, chiều sáng/tối và min_area; 100000 lớn hơn ảnh mẫu 36864 pixel |
| Quá nhiều vật thể | Marker có thể quá dày; xem raw/hmax, h, nhiễu, mask |
| Hai vật thể bị gộp | Thiếu marker hoặc mask nối vùng; xem distance, điều chỉnh h có kiểm soát |
| Nhãn đúng khác kích thước | Chọn nhãn tương ứng; chương trình không tự resize vì làm sai đánh giá |
| Study từ chối thư mục | Đổi tên output mới; không trộn đợt đã có study.json |
| Chạy lâu | Bắt đầu `--limit 1`; custom là Python tự cài. Chạy tuần tự, không mở nhiều đợt cùng lúc |

Để dừng lệnh đang chạy, bấm Ctrl+C ở cửa sổ đang chạy. Không End task các tiến trình hệ thống không liên quan. Trong app có nút Dừng tác vụ. Các tiến trình Java do bộ điều phối tạo được thu hồi khi kết thúc/hủy.

## 11. Kịch bản demo trước thầy (khoảng 5–7 phút)

1. Mở báo cáo/slide, nói tên đề tài và mục tiêu tách từng đối tượng.
2. Mở ảnh mẫu: chỉ 7 vật thể và hai cặp chạm nhau; mở kết quả CCL=5, hmax=7.
3. Chỉ các ảnh mask → distance → marker → labels và giải thích vì sao dùng −distance.
4. Mở code Watershed và reconstruction; nêu phần tự cài và phần dùng thư viện.
5. Chạy script Groovy trong Fiji, mở kết quả; chỉ file `fiji_metrics.csv` và điểm Python.
6. Mở bảng 50 ảnh test, chỉ F1 của bốn cách chạy, giải thích vì sao native khác tiền xử lý.
7. Mở bảng ablation: raw marker chia thừa, CCL tốt hơn baseline ở tập khảo sát; nêu hạn chế.
8. Chỉ bộ kiểm thử và thư mục cấu hình, nhật ký để người khác tái lập.

Có thể mở MorphoLab cuối buổi bằng `python -m morpholab gui` để giới thiệu điểm nhấn giao diện. Nó dùng cùng phần lõi, không thay thế việc hiểu lý thuyết, mã nguồn và thí nghiệm.

## 12. Hồ sơ nộp và tự kiểm tra trước khi nộp

- `submission/BAO_CAO_NHOM_1.docx`: báo cáo sửa được; bản PDF đi kèm để giữ bố cục.
- `submission/PRESENTATION_NHOM_1.pptx`: 10 slide, có ghi chú thuyết trình.
- `submission/THUYET_TRINH.md`: lời dẫn và nguồn theo từng slide.
- `submission/HUONG_DAN_CHAY_VA_TEST.md`: tài liệu này.
- Repository chứa code Python, Java, Groovy, cấu hình, tests và CSV/biểu đồ trong `docs/evidence`.

Nhóm đọc lại tên/MSSV, kiểm tra deadline đúng năm và giờ trên LMS, mở file trên máy trình chiếu, chạy lại demo và luyện giải thích. Phần phân công trong báo cáo là đề xuất: sửa theo đóng góp thực tế trước khi nộp. Một đại diện gửi link repository và báo cáo/slide theo yêu cầu LMS, ghi **Nhóm 1**. Việc nộp LMS chưa được thực hiện tự động.
