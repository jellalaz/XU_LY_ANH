"""Xuất phiếu HTML xem kết quả; báo cáo nộp chính nằm ở submission/latex/main.tex."""
from pathlib import Path
from html import escape
import base64
import io
import json
from PIL import Image


def _page(title,body):
    return '''<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>'''+escape(title)+'''</title><style>
body{font:16px/1.6 system-ui,sans-serif;margin:40px auto;max-width:1180px;padding:0 24px;color:#18313c;background:#f5f8fa}
h1,h2{color:#133d4a}header{border-bottom:4px solid #26a78e}article{background:white;padding:22px;margin:20px 0;border-radius:12px}
table{border-collapse:collapse;width:100%;font-size:14px}th,td{padding:8px;border-bottom:1px solid #d8e3e8;text-align:left}
th{background:#e1f2ef}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#edf3f6;padding:16px;font-size:12px}
.gallery{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:18px}img{max-width:100%;height:auto}
.scroll{overflow-x:auto}.note{color:#536d79}@media print{body{background:white;margin:0}article{break-inside:avoid}}
</style><header><p>MORPHOLAB · PTIT NHÓM 1</p><h1>'''+escape(title)+'''</h1></header>'''+body+'''<p class="note">Phiếu thí nghiệm xuất tự động; cần bổ sung phân tích để biên soạn báo cáo môn học.</p></html>'''


def _image(path,title):
    path=Path(path)
    if not path.exists(): return ''
    with Image.open(path) as image:
        image.thumbnail((1000,750)); data=io.BytesIO(); image.convert('RGB').save(data,format='PNG')
    encoded=base64.b64encode(data.getvalue()).decode('ascii')
    return '<figure><img alt="'+escape(title,quote=True)+'" src="data:image/png;base64,'+encoded+'"><figcaption>'+escape(title)+'</figcaption></figure>'


def session_report(folder):
    """Tạo trang HTML của một lần chạy, gồm ảnh và thông số."""
    folder=Path(folder)
    data=json.loads((folder/'run.json').read_text(encoding='utf-8'))
    body='<article><h2>Kết quả phân đoạn</h2><p>Số đối tượng: <b>'+str(int(data['objects']))+'</b></p>'
    body+='<div class="gallery">'+_image(folder/'overlay.png','Kết quả chồng lên ảnh gốc')+_image(folder/'labels_rgb.png','Nhãn từng đối tượng')+'</div></article>'
    metricfile=folder/'metrics.json'
    if metricfile.exists():
        metrics=json.loads(metricfile.read_text(encoding='utf-8'))
        body+='<article><h2>Đánh giá so với ground truth</h2><table>'
        body+=''.join('<tr><th>'+escape(str(k))+'</th><td>'+escape(str(v))+'</td></tr>' for k,v in metrics.items())+'</table></article>'
    body+='<article><h2>Cấu hình và nguồn dữ liệu</h2><pre>'+escape(json.dumps(data,ensure_ascii=False,indent=2))+'</pre></article>'
    from .io import object_table,read_labels,read_image
    objects=object_table(read_labels(folder/'labels.tif'),read_image(folder/'input.tif'))
    body+='<article><h2>Thống kê đối tượng</h2><p>Đơn vị pixel / pixel²; hiển thị tối đa 200 dòng. CSV chứa toàn bộ.</p><div class="scroll">'+objects.head(200).to_html(index=False,escape=True)+'</div></article>'
    path=folder/'report.html'; path.write_text(_page('Phiếu kết quả phân đoạn',body),encoding='utf-8'); return path


def study_report(folder):
    """Tạo trang HTML tổng hợp một đợt nghiên cứu từ CSV đã lưu."""
    import pandas as pd
    folder=Path(folder)
    metadata=json.loads((folder/'study.json').read_text(encoding='utf-8'))
    summary=pd.read_csv(folder/'summary.csv')
    body='<article><h2>Tóm tắt thí nghiệm</h2><p>'+escape(metadata['description'])+'</p><p>Trạng thái: '+escape(metadata['status'])+'</p>'
    body+='<div class="scroll">'+summary.to_html(index=False,float_format=lambda x:f'{x:.4f}',na_rep='—',escape=True)+'</div></article>'
    body+='<article>'+_image(folder/'quality.png','Chất lượng phân đoạn theo cấu hình')+'</article>'
    body+='<article><h2>Quy ước thời gian và đánh giá</h2><p>Metric là macro mean theo ảnh, ghép đối tượng tại IoU ≥ 0.5. Fiji shared chỉ đo bước Watershed với đầu vào chung. Native là workflow độc lập; thời gian có xuất ảnh trung gian. Không so các loại thời gian này như cùng một phép đo.</p><p>Dữ liệu test chỉ dùng đánh giá; kế hoạch này không tự chọn tham số từ test.</p><pre>'+escape(json.dumps(metadata,ensure_ascii=False,indent=2))+'</pre></article>'
    galleries=''.join(_image(p,p.parent.name+' / '+p.stem) for p in sorted((folder/'gallery').glob('*/*.png'))[:12])
    if galleries: body+='<article><h2>Một số ảnh minh họa</h2><div class="gallery">'+galleries+'</div></article>'
    path=folder/'report.html'; path.write_text(_page('Phiếu thực nghiệm và kiểm chứng',body),encoding='utf-8'); return path
