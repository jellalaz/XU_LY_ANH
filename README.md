# Xử lý ảnh PTIT nhóm 1

Nghiên cứu, cài đặt, thực nghiệm và đánh giá **phân đoạn đối tượng bằng hình thái học toán học và Watershed**, sử dụng **MorphoLibJ trên Fiji/ImageJ** làm nền tảng tham chiếu và kiểm chứng.

## Phạm vi và sản phẩm

Nội dung gồm erosion, dilation, opening, closing, morphological reconstruction, distance transform, watershed và connected components. Cần có lý thuyết, cài đặt lại thuật toán bằng Python, thực nghiệm trên Fiji/ImageJ và đánh giá định lượng.

Sản phẩm theo đề bài: báo cáo khoảng 30 trang và presentation khoảng 10 slides. Một đại diện nộp link lên LMS, ghi rõ mã nhóm. Deadline người dùng cung cấp: **19/11**, chưa nêu năm hoặc giờ đóng bài. Bài tập lớn chiếm 50% điểm bài tập.

## Thành viên theo ảnh đề tài

| Mã sinh viên | Họ và tên |
| --- | --- |
| B23DCCN254 | Kiều Trường Giang |
| B23DCCN667 | Trần Đỗ Lan Phương |
| B23DCCN814 | Giang Thùy Tiên |
| B23DCCN954 | Phạm Văn Vỹ |

## Tổ chức tài liệu

- `docs/NGHIEN_CUU.md`: ghi chú nền tảng, hướng thực nghiệm và tiêu chí kiểm chứng.
- `materials/SOURCES.md`: nguồn tài liệu và trạng thái truy cập.
- `materials/downloads/`: tài liệu tham khảo tải về, lưu cục bộ và được Git bỏ qua.
- `materials/metadata/`: văn bản trích xuất, ảnh xem trang và thông tin kiểm tra tệp, lưu cục bộ.

Repository: [jellalaz/XU_LY_ANH](https://github.com/jellalaz/XU_LY_ANH). Thư mục làm việc đã clone từ repository này; remote `origin` dùng cùng URL cho fetch và push.

## Mở phần mềm

Nhấp đúp `launch_app.cmd` trong thư mục dự án. Launcher sử dụng env Miniconda `ai` tại `%USERPROFILE%\miniconda3\envs\ai`. Cũng có thể mở Anaconda Prompt:

```bat
conda activate ai
cd /d D:\XU_LY_ANH
python -m morpholab gui
```

Chọn **Ảnh mẫu có nhãn → Phân đoạn**, sau đó sang tab **Fiji & đánh giá → Chạy Fiji / MorphoLibJ**. Chương trình có giao diện tiếng Việt, dùng chung phần lõi với CLI.

## Phiên bản tích hợp 1.2

Sáu tab gồm **Phân đoạn**, **Fiji & đánh giá**, **Benchmark**, **Nghiên cứu**, **Phiên đã lưu** và **Hướng dẫn**. Bạn điều khiển Python và Fiji từ một ứng dụng; Fiji được gọi bằng tiến trình Java khi cần và vẫn có script riêng để kiểm chứng trong Fiji. Không cần train mô hình AI.

- Duyệt ảnh và nhãn đúng theo dataset/split; chỉnh marker bằng chuột; xem bảng thuộc tính đối tượng.
- Kế hoạch `compare` so sánh cả bốn cách chạy; `ablation` đo ảnh hưởng khi bỏ từng bước; `robustness` kiểm tra nhiễu và độ mờ với seed cố định.
- Lưu phiên đầy đủ và mở lại ảnh, cấu hình, ground truth, kết quả Python/Fiji mà không phải tính lại.
- Phiếu HTML độc lập có hình, bảng, cấu hình và môi trường; mở được từ app hoặc in qua trình duyệt. Đây là phiếu thực nghiệm, chưa phải báo cáo cuối kỳ hoàn chỉnh.
- Nút **Dừng tác vụ** và đóng cửa sổ gửi tín hiệu hủy, chờ thu hồi tiến trình Fiji. Chạy tuần tự từng ảnh; JVM giới hạn heap 512 MB, không phải giới hạn toàn bộ RAM của tiến trình.

Giao diện có giải thích ngắn bằng tiếng Việt ngay cạnh thuật ngữ tiếng Anh, cảnh báo kết quả rỗng hoặc chưa chạy lại, và nút khôi phục cấu hình mặc định. Khảo sát h chạy đúng engine đang chọn và xuất cấu hình hmax tương ứng.

Đã chạy qua 29 kiểm thử, gồm 7 luồng giao diện Tk thực và tích hợp Fiji. [Biên bản kiểm tra phần mềm](docs/KIEM_THU_PHAN_MEM.md) ghi rõ cách chạy và giới hạn. Đã đối chiếu đủ 50 ảnh test BBBC039 bằng Python tự cài, thư viện, Fiji shared và Fiji native (200 kết quả, không lỗi), cùng 84 kết quả ablation/robustness trên 6 ảnh validation.

Ứng dụng là công cụ hỗ trợ nghiên cứu và minh họa. Đề bài yêu cầu lý thuyết, cài đặt, kiểm chứng Fiji, thực nghiệm, báo cáo và slide; không bắt buộc giao diện tích hợp, cũng không nêu điểm cộng riêng cho giao diện.

```bat
python -m morpholab study data\bbbc039\manifest.json --kind compare --split test --limit 50 --repeats 1 --out outputs\compare_new
python -m morpholab study data\bbbc039\manifest.json --config configs\research_library.json --kind ablation --limit 6 --repeats 1 --out outputs\ablation_new
python -m morpholab study data\bbbc039\manifest.json --config configs\research_library.json --kind robustness --limit 6 --repeats 1 --out outputs\robustness_new
```

Thư mục xuất study mới phải chưa chứa `study.json`; các kết quả hoàn tất được giữ để tránh trộn dữ liệu. Khi hủy tác vụ, kết quả từng cấu hình đã hoàn tất vẫn được lưu và đánh dấu `cancelled`; chưa hỗ trợ tiếp tục tự động một study bị dừng.

## Chức năng đã có

- Cài đặt Python riêng cho co, giãn, mở, đóng, reconstruction bằng hàng đợi, distance transform Euclid, BFS gán nhãn và Watershed bằng hàng đợi ưu tiên.
- Bản SciPy/scikit-image để đối chiếu và benchmark. Gaussian, Otsu, đọc/ghi ảnh và thống kê dùng thư viện ở cả hai bản; phần tự cài đặt được tách rõ trong `morpholab/algorithms.py`.
- Xem từng bước, phóng to, chọn đối tượng để xem diện tích và tâm; thay tham số; lưu/nạp cấu hình.
- Kiểm chứng bằng Fiji/MorphoLibJ thật với cùng elevation/marker/mask. Có thêm workflow Fiji độc lập từ ảnh đầu vào, xuất đủ các toán tử hình thái.
- Nạp ground truth, tính IoU/Dice, precision/recall/F1 theo đối tượng, PQ, sai số đếm, chẩn đoán split/merge.
- Xử lý thư mục ảnh; benchmark có warm-up và lặp đo; khảo sát h chỉ trên validation; xuất CSV, JSON, TIFF và biểu đồ PNG.
- Bộ ảnh tổng hợp tái lập bằng seed và bộ ảnh thật BBBC039 có phân chia chính thức.

Hướng dẫn chi tiết: [Sử dụng phần mềm](docs/HUONG_DAN.md). Phạm vi đáp ứng đề bài và cách kiểm chứng: [Đối chiếu yêu cầu](docs/DOI_CHIEU_YEU_CAU.md). Kết quả đo: [Thực nghiệm](docs/THUC_NGHIEM.md).

## Chạy bằng lệnh

```bat
python -m morpholab dataset synthetic
python -m morpholab dataset bbbc039
python -m morpholab segment data\synthetic\synth_00.tif --truth data\synthetic\synth_00_gt.tif --out outputs\demo --fiji
python -m morpholab segment data\synthetic\synth_00.tif --truth data\synthetic\synth_00_gt.tif --out outputs\native --fiji-native
python -m morpholab benchmark data\synthetic\manifest.json --limit 3 --repeats 3
python -m unittest discover -s tests -v
```

## Môi trường

Python 3.11, các thư viện trong `requirements.txt`; Tkinter đi kèm env Miniconda đã có trên máy. Bản khóa các thư viện trực tiếp đã kiểm tra nằm trong `requirements-lock.txt`. Fiji mặc định `C:\Tools\Fiji`, có Java JDK và `plugins/MorphoLibJ_-1.6.5.jar`; có thể chọn đường dẫn khác trên giao diện.

## Phạm vi bàn giao

Ứng dụng và chương trình thực nghiệm đã triển khai. Báo cáo khoảng 30 trang và slides khoảng 10 trang là sản phẩm viết riêng; chưa được soạn thành bản nộp hoàn chỉnh. Thí nghiệm có kết quả thực đo, bao gồm trường hợp phương pháp mở rộng chưa tốt hơn baseline; không khẳng định phương pháp luôn đúng hoặc luôn cải thiện.
