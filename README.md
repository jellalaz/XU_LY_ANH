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
