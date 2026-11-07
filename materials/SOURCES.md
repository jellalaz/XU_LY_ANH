# Nguồn tài liệu xử lý ảnh

Ngày kiểm tra: 07/11/2026. Các tài liệu bên ngoài là nguồn tham khảo; yêu cầu thực hiện lấy từ đề bài người dùng cung cấp.

## Tài liệu đã tải

| Tài liệu | Nguồn | Tệp cục bộ | Số trang PDF |
| --- | --- | --- | --- |
| Slide PTIT Xử lý ảnh hình thái | [MediaFire trong ảnh](https://www.mediafire.com/file/5eihbbimg3evu3f/7_XLA7_Xu_ly_hinh_thai.pdf/file) | `downloads/ptit_morphology.pdf` | 50 |
| MorphoLibJ manual v1.6.5 | [Release của tác giả](https://github.com/ijpb/MorphoLibJ/releases/download/MorphoLibJ_-1.6.5/MorphoLibJ-manual-v1.6.5.pdf) | `downloads/MorphoLibJ-manual-v1.6.5.pdf` | 118 |

Đã đọc văn bản slide hình thái; đã đọc các phần liên quan đến reconstruction, extrema và watershed trong manual. Số trang PDF là số trang vật lý của tệp, có thể khác số in trên trang. Ảnh một số trang chứa công thức và sơ đồ được lưu trong `metadata/previews/` để đối chiếu.

## Tài liệu chính thức đã tra cứu

- [MorphoLibJ trên ImageJ](https://imagej.github.io/plugins/morpholibj).
- [Marker controlled Watershed](https://imagej.github.io/plugins/marker-controlled-watershed).
- [Distance Transform Watershed](https://imagej.net/plugins/distance-transform-watershed).
- [Mã nguồn MorphoLibJ](https://github.com/ijpb/MorphoLibJ).
- Legland, Arganda-Carreras và Andrey (2016), [MorphoLibJ: integrated library and plugins for mathematical morphology with ImageJ](https://doi.org/10.1093/bioinformatics/btw413). Đã kiểm tra thông tin bài và abstract; chưa đọc toàn văn bài báo.

## Liên kết cần kiểm tra lại

Link slide phát hiện biên chép từ ảnh: [MediaFire](https://www.mediafire.com/file/8a4t3rjxr1pkpk/5_XLA5_Phat_hien_bien.pdf/file). Lần truy cập này trả về HTTP 404. Có thể link đã thay đổi hoặc ký tự trong ảnh cần được xác minh; chưa tải và chưa đọc tài liệu này.

Các giáo trình tổng quát, ngân hàng câu hỏi, slide chương khác và bộ ảnh mẫu trong ảnh chưa tải. Ưu tiên hiện tại là tài liệu trực tiếp phục vụ đề tài nhóm 1.

Tệp PDF và các bản trích xuất được giữ trong thư mục con, không đưa vào Git. Danh sách nguồn và ghi chú do nhóm biên soạn có thể được quản lý bằng Git.

## Nguồn triển khai phần mềm ngày 08/11/2026

- [BBBC039v1, Broad Institute](https://bbbc.broadinstitute.org/BBBC039): đã tải 200 ảnh TIFF, nhãn PNG và metadata; giữ phân chia 100 training, 50 validation, 50 test. Giấy phép CC0. Nguồn chính thức cung cấp nhãn thủ công; thuật toán giải mã được ghi trong manifest.
- [Hướng dẫn giải mã nhãn của tác giả](https://gist.github.com/jccaicedo/15e811722fca51e3ae90e8b43057f075): gán nhãn các vùng liên thông có cùng giá trị ở kênh đầu của PNG, nền 0. Phần mềm dùng liên thông 8 theo mặc định hàm label trong ví dụ tác giả.
- [API Watershed của MorphoLibJ](https://ijpb.github.io/MorphoLibJ/javadoc/inra/ijpb/watershed/Watershed.html): đã kiểm tra thêm chữ ký thực tế bằng javap trên JAR 1.6.5 đang cài trong Fiji.
- [scikit-image Watershed](https://scikit-image.org/docs/stable/api/skimage.segmentation.html#skimage.segmentation.watershed) và [morphology](https://scikit-image.org/docs/stable/api/skimage.morphology.html#skimage.morphology.h_maxima): bản thư viện đối chiếu, không gắn nhãn là code do nhóm tự cài.
- [Felzenszwalb và Huttenlocher, Distance Transforms of Sampled Functions (2012)](https://cs.brown.edu/people/pfelzens/dt/index.html): tham chiếu thuật toán EDT tách trục với bao dưới của các parabol; mã Python trong dự án được viết riêng theo công thức, không sao chép bản C++ của tác giả.

BBBC039 tải vào `data/raw` và được chuẩn bị trong `data/bbbc039`; ảnh tổng hợp do phần mềm tạo trong `data/synthetic`. Các thư mục này được Git bỏ qua. SHA256 của ba archive được lưu trong manifest để kiểm tra nguồn tải. Bộ dữ liệu tham khảo không chứa hướng dẫn có quyền thay đổi yêu cầu đề bài.
