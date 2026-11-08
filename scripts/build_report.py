"""Build the editable academic report from its reviewed Vietnamese source."""
from pathlib import Path
import ast,csv,json,re
from docx import Document
from docx.shared import Cm,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'submission'; DEST.mkdir(exist_ok=True)
doc=Document(); sec=doc.sections[0]
sec.page_width=Cm(21);sec.page_height=Cm(29.7)
sec.top_margin=Cm(2);sec.bottom_margin=Cm(2);sec.left_margin=Cm(2.4);sec.right_margin=Cm(2)
for name in ('Normal','Title','Heading 1','Heading 2','Caption'):
    st=doc.styles[name];st.font.name='Times New Roman';st.font.color.rgb=RGBColor(0,0,0)
doc.styles['Normal'].font.size=Pt(12)
doc.styles['Normal'].paragraph_format.line_spacing=1.12
doc.styles['Normal'].paragraph_format.space_after=Pt(7)
doc.styles['Heading 1'].font.size=Pt(17)
doc.styles['Heading 1'].paragraph_format.space_after=Pt(12)
doc.styles['Title'].font.size=Pt(25)
header=sec.header.paragraphs[0];header.text='PTIT  •  Xử lý ảnh  •  Nhóm 1';header.style='Caption'
footer=sec.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.RIGHT
footer.add_run('Nhóm 1   |   ')
field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');footer._p.append(field)
source=(DEST/'report_source.md').read_text(encoding='utf-8'); pages=source.split('---PAGE---')
titles=[re.search(r'^# (.+)',page.strip()).group(1) for page in pages]
code=(ROOT/'morpholab/algorithms.py').read_text(encoding='utf-8'); tree=ast.parse(code)
functions={n.name:ast.get_source_segment(code,n) for n in tree.body if isinstance(n,ast.FunctionDef)}

def para(text,style=None):
    p=doc.add_paragraph(text,style);return p

def listing(text):
    p=doc.add_paragraph();p.paragraph_format.space_after=Pt(6)
    p.paragraph_format.line_spacing=1
    p.paragraph_format.keep_together=True
    r=p.add_run(text);r.font.name='Consolas';r.font.size=Pt(8)
    return p

def table(headers,rows):
    t=doc.add_table(rows=1,cols=len(headers));t.autofit=True
    for cell,text in zip(t.rows[0].cells,headers):cell.text=str(text)
    for row in rows:
        for cell,value in zip(t.add_row().cells,row):cell.text=str(value)
    for ri,row in enumerate(t.rows):
        for cell in row.cells:
            pr=cell._tc.get_or_add_tcPr();border=OxmlElement('w:tcBorders')
            for edge in ('top','left','bottom','right'):
                e=OxmlElement('w:'+edge);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'D9D9D9');border.append(e)
            pr.append(border)
            sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'DCE6F1' if ri==0 else ('F4F6F8' if ri%2 else 'FFFFFF'));pr.append(sh)
            for p in cell.paragraphs:
                p.paragraph_format.space_after=Pt(4);p.paragraph_format.space_before=Pt(4)
                for r in p.runs:r.font.size=Pt(10);r.bold=ri==0
    return t

def directive(line):
    if line=='@TOC':
        for i,title in enumerate(titles[2:],3):
            p=para(f'{i:02d}   {title}');p.paragraph_format.space_after=Pt(2)
            for r in p.runs:r.font.size=Pt(10)
        para('Các số trên đánh dấu thứ tự phần nội dung; xem số trang ở chân trang.')
    elif line.startswith('@EQ '):
        p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        math=OxmlElement('m:oMath');r=OxmlElement('m:r');t=OxmlElement('m:t');t.text=line[4:];r.append(t);math.append(r);p._p.append(math)
    elif line.startswith('@CODE '):
        text=functions[line.split()[1]]
        lines=[l for l in text.splitlines() if not l.strip().startswith('#')]
        listing('\n'.join(lines))
    elif line.startswith('@IMAGE '):
        path=ROOT/line[7:]
        if not path.exists():raise FileNotFoundError(path)
        doc.add_picture(str(path),width=Cm(16))
    elif line.startswith('@TABLE '):
        _,path,kind=line.split();rows=list(csv.DictReader((ROOT/path).open(encoding='utf-8-sig')))
        if kind=='compare':
            table(['Cách chạy','Ảnh','F1','CI 95%','IoU','Sai số đếm'],[[r['variant'],r['images'],f"{float(r['object_f1']):.4f}",f"{float(r['ci_low']):.4f}–{float(r['ci_high']):.4f}",f"{float(r['foreground_iou']):.4f}",f"{float(r['count_mae']):.2f}"] for r in rows])
        elif kind in ('ablation','robustness'):
            table(['Biến thể','F1','IoU','Sai số đếm'],[[r['variant'],*[f'{float(r[k]):.4f}' for k in ('object_f1','foreground_iou','count_mae')]] for r in rows])
        else:table(['Cạnh ảnh','Cách cài','Trung vị s','Min s','Max s'],[[r['size'],r['method'],*[f'{float(r[k]):.6f}' for k in ('median','min','max')]] for r in rows])
    elif line=='@MATRICES':
        data=json.loads((ROOT/'docs/evidence/academic_checks/hand_examples.json').read_text())
        table(['A','Erosion','Dilation'],[['\n'.join(' '.join(map(str,row)) for row in data[k]) for k in ('input','erosion','dilation')]])
    elif line=='@PARAMETERS':
        data=json.loads((ROOT/'configs/default.json').read_text());table(['Tham số','Giá trị'],list(data.items()))
    elif line=='@NATIVE_DIFFERENCES':
        table(['Bước','Python mặc định','Fiji native'],[['Cường độ','float chuẩn hóa','Lượng tử hóa 8-bit'],['SE','Đĩa r=1','Vuông r=1'],['Khoảng cách','Euclid tách trục','ImageJ EDM'],['Cực đại','h-maxima tự cài/thư viện','MorphoLibJ extended maxima'],['Lấp lỗ','Liên thông đã chọn','Mặc định plugin'],['Đo thời gian','Không đọc ghi','Có ghi ảnh trung gian']])
    elif line=='@FIJI_SCRIPT':listing((ROOT/'fiji/ReplayWatershed.groovy').read_text(encoding='utf-8'))
    elif line=='@TEST_COMMANDS':listing('conda activate ai\ncd /d D:\\XU_LY_ANH\npython -B -m unittest discover -s tests -v\npython -B scripts/academic_checks.py\n\nREM Chay them 7 test Tk tren Windows\nset MORPHOLAB_DESKTOP_TEST=1\npython -B -m unittest discover -s tests -v\nset MORPHOLAB_DESKTOP_TEST=')
    elif line=='@RUN_COMMANDS':listing('conda activate ai\ncd /d D:\\XU_LY_ANH\npython -m morpholab dataset synthetic\npython -m morpholab segment data\\synthetic\\synth_00.tif ^\n  --truth data\\synthetic\\synth_00_gt.tif ^\n  --out outputs\\demo_shared --fiji\npython -m morpholab segment data\\synthetic\\synth_00.tif ^\n  --truth data\\synthetic\\synth_00_gt.tif ^\n  --out outputs\\demo_native --fiji-native\npython -m morpholab benchmark data\\synthetic\\manifest.json ^\n  --limit 1 --repeats 3 --out outputs\\demo_benchmark')
    elif line=='@REQUIREMENTS':table(['Yêu cầu','Minh chứng bàn giao'],[['Lý thuyết đủ sâu','Định nghĩa, công thức, ví dụ và độ phức tạp trong báo cáo'],['Plugin Fiji','MorphoLibJ; shared và native; script Groovy'],['Cài đặt lại','morpholab/algorithms.py, pipeline.py; Java adapter'],['Định lượng hai nền tảng','Python metric và fiji_metrics.csv từ Java'],['Thực nghiệm và tối ưu','50 test × 4 cách; ablation, stress test; đo reconstruction'],['Báo cáo và presentation','Báo cáo này, bộ slide 10 trang, ghi chú thuyết trình'],['Hướng dẫn tái lập','submission/HUONG_DAN_CHAY_VA_TEST.md']])
    else:raise ValueError(line)

for index,page in enumerate(pages):
    if index:doc.add_page_break()
    for block in page.strip().split('\n\n'):
        if block.startswith('# '):
            lines=block.splitlines();para(lines[0][2:],'Title' if index==0 else 'Heading 1')
            for line in lines[1:]:
                if line.startswith('@'):directive(line)
                elif line.strip():para(line)
        elif block.startswith('@'):
            for line in block.splitlines():
                if line.startswith('@'):directive(line)
                elif line.strip():para(line,'Caption')
        else:para(block)
doc.core_properties.title='Phân đoạn đối tượng bằng hình thái học toán học và Watershed'
doc.core_properties.author='PTIT Nhóm 1'
doc.save(DEST/'BAO_CAO_NHOM_1.docx')
print(f'{len(pages)} sections -> {DEST / "BAO_CAO_NHOM_1.docx"}')
