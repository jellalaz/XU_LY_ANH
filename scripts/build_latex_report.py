"""Generate the editable LaTeX academic report and data tables."""
from pathlib import Path
import re,csv,json,ast,shutil
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'submission/latex';OUT.mkdir(exist_ok=True)
(OUT/'code').mkdir(exist_ok=True)
source=(ROOT/'submission/report_source.md').read_text(encoding='utf-8-sig')
pages=source.split('---PAGE---')
sections={re.search(r'^# (.+)',p.strip()).group(1):p.strip().split('\n',1)[1].strip() for p in pages}
mapping={'&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','{':r'\{','}':r'\}','~':r'\textasciitilde{}','^':r'\textasciicircum{}','\\':r'\textbackslash{}'}
symbols={'∈':r'\ensuremath{\in}','≤':r'\ensuremath{\leq}','≥':r'\ensuremath{\geq}','×':r'\ensuremath{\times}','→':r'\ensuremath{\to}','−':'-','²':r'\ensuremath{^2}','⁹':r'\ensuremath{^9}','⁻':r'\ensuremath{^-}','α':r'\ensuremath{\alpha}','σ':r'\ensuremath{\sigma}','δ':r'\ensuremath{\delta}','∞':r'\ensuremath{\infty}'}
def esc(text):
    text=''.join(symbols.get(c,mapping.get(c,c)) for c in str(text))
    return re.sub(r'\[([1-8])\]',lambda m:r'\cite{ref'+m[1]+'}',text)

def fig(file,caption,label,width=r'\linewidth'):
    return '\n'+r'\begin{figure}[H]\centering'+'\n'+r'\includegraphics[width='+width+']{figures/'+file+'}\n'+r'\caption{'+esc(caption)+'}'+r'\label{fig:'+label+'}\n'+r'\end{figure}'+'\n'
def table(headers,rows,caption,label):
    cols=' '.join('X' for _ in headers)
    if label=='compare':cols=r'p{0.21\linewidth} p{0.05\linewidth} X p{0.22\linewidth} X X'
    if label in ('ablation','robustness'):cols=r'p{0.35\linewidth} X X X'
    if label=='timing':cols=r'p{0.10\linewidth} p{0.30\linewidth} X X X'
    out=r'\begin{table}[H]\centering\small'+'\n'+r'\caption{'+esc(caption)+'}'+r'\label{tab:'+label+'}\n'+r'\begin{tabularx}{\linewidth}{'+cols+'}\n'+r'\toprule'+'\n'
    out+=' & '.join(r'\textbf{'+esc(h)+'}' for h in headers)+r' \\ \midrule'+'\n'
    out+='\n'.join(' & '.join(esc(v) for v in row)+r' \\' for row in rows)
    return out+'\n'+r'\bottomrule\end{tabularx}\end{table}'+'\n'
eq=[r'\mathcal{N}_4(x,y)=\{(x-1,y),(x+1,y),(x,y-1),(x,y+1)\}',r'\mathcal{N}_8(x,y)=\mathcal{N}_4(x,y)\cup\{(x\pm1,y\pm1)\}',r'A\ominus B=\{x:x+B\subseteq A\}',r'A\oplus B=\{a+b:a\in A,b\in B\}',r'A\circ B=(A\ominus B)\oplus B',r'A\bullet B=(A\oplus B)\ominus B',r'X_0=M,\quad X_{k+1}=\min(\delta(X_k),F),\quad R_F^\delta(M)=X_k\ \text{khi }X_{k+1}=X_k',r'L(p)=L(q)\quad\text{nếu }p,q\text{ thuộc cùng thành phần liên thông của mask}',r'D(p)=\min_{q\notin A}\lVert p-q\rVert_2',r'D^2(x,y)=\min_{(u,v)\text{ là nền}}\big((x-u)^2+(y-v)^2\big)',r's=\frac{(f(j)+j^2)-(f(i)+i^2)}{2(j-i)}',r'R=R_D^\delta(D-h),\quad H_h=\{p:D(p)-R(p)\geq h\}',r'\operatorname{cost}(q)=\max(\operatorname{cost}(p),E(q))',r'\mathrm{IoU}=\frac{|P\cap G|}{|P\cup G|},\qquad\mathrm{Dice}=\frac{2|P\cap G|}{|P|+|G|}',r'\mathrm{Precision}=\frac{TP}{TP+FP},\quad\mathrm{Recall}=\frac{TP}{TP+FN},\quad F_1=\frac{2TP}{2TP+FP+FN}',r'\mathrm{PQ}=\frac{\sum_{\text{cặp đúng}}\mathrm{IoU}}{TP+0.5FP+0.5FN}']
eq_lines=[l[4:] for l in source.splitlines() if l.startswith('@EQ ')]
EQ=dict(zip(eq_lines,eq)); assert len(EQ)==len(eq)
code=(ROOT/'morpholab/algorithms.py').read_text(encoding='utf-8');tree=ast.parse(code)
for n in tree.body:
    if isinstance(n,ast.FunctionDef) and n.name in ['reconstruction_dilation','connected_components','_squared_edt_1d','watershed']:
        text=ast.get_source_segment(code,n)
        # Listings omit comments/docstrings only; executable statements stay exact.
        lines=text.splitlines()
        if n.body and isinstance(n.body[0],ast.Expr) and isinstance(n.body[0].value,ast.Constant) and isinstance(n.body[0].value.value,str):
            first=n.body[0];del lines[first.lineno-n.lineno:first.end_lineno-n.lineno+1]
        text='\n'.join(line for line in lines if line.strip() and not line.lstrip().startswith('#'))
        (OUT/'code'/(n.name+'.py')).write_text(text,encoding='utf-8')
shutil.copyfile(ROOT/'fiji/ReplayWatershed.groovy',OUT/'code/ReplayWatershed.groovy')

def directive(line):
    if line.startswith('@EQ '):return r'\begin{equation}'+EQ[line[4:]]+r'\end{equation}'
    if line.startswith('@CODE '):
        name=line.split()[1]
        return r'\lstinputlisting[caption={Trích mã tự cài: '+esc(name)+'},label={lst:'+name+'}]{code/'+name+'.py}'
    if line.startswith('@TABLE '):
        _,path,kind=line.split();rows=list(csv.DictReader((ROOT/path).open(encoding='utf-8-sig')))
        if kind=='compare':return table(['Cách chạy','Ảnh','F1','CI 95%','IoU','MAE đếm'],[[r['variant'],r['images'],f"{float(r['object_f1']):.4f}",f"{float(r['ci_low']):.4f}–{float(r['ci_high']):.4f}",f"{float(r['foreground_iou']):.4f}",f"{float(r['count_mae']):.2f}"] for r in rows],'Đối chiếu trên 50 ảnh test BBBC039; trung bình theo ảnh.','compare')
        if kind in ['ablation','robustness']:return table(['Biến thể','F1','IoU','MAE đếm'],[[r['variant'].replace('_',' '),*[f'{float(r[k]):.4f}' for k in ('object_f1','foreground_iou','count_mae')]] for r in rows],('Loại/thay từng bước' if kind=='ablation' else 'Nhiễu và làm mờ')+' trên 6 ảnh validation.',kind)
        return table(['Cạnh ảnh','Cách cài','Trung vị (s)','Min (s)','Max (s)'],[[r['size'],r['method'].replace('_',' '),*[f'{float(r[k]):.6f}' for k in ('median','min','max')]] for r in rows],'Thời gian reconstruction: 5 lần đo sau 1 warm-up, đầu ra bằng nhau.','timing')
    if line=='@MATRICES':
        data=json.loads((ROOT/'docs/evidence/academic_checks/hand_examples.json').read_text());out=''
        for key,title in [('input','A'),('erosion',r'A\ominus B'),('dilation',r'A\oplus B')]:
            out+=title+'=\\begin{bmatrix}'+'\\\\'.join('&'.join(map(str,row)) for row in data[key])+r'\end{bmatrix}\quad '
        return r'\begin{equation}\resizebox{0.92\linewidth}{!}{$ '+out+r'$}\end{equation}'
    if line=='@PARAMETERS':return table(['Tham số','Giá trị'],json.loads((ROOT/'configs/default.json').read_text()).items(),'Cấu hình Python mặc định dùng trong đối chiếu chính.','parameters')
    if line=='@NATIVE_DIFFERENCES':return table(['Bước','Python mặc định','Fiji native'],[['Cường độ','Float chuẩn hóa','8-bit'],['SE','Đĩa r=1','Vuông r=1'],['Khoảng cách','Euclid tách trục','ImageJ EDM'],['Cực đại','h-maxima','Extended maxima'],['Lấp lỗ','Liên thông đã chọn','Mặc định plugin'],['Thời gian','Không đọc ghi','Có ghi TIFF']],'Những khác biệt cần kiểm soát khi diễn giải kết quả.','native')
    if line=='@FIJI_SCRIPT':return r'\lstinputlisting[language=Java,caption={Script Groovy chạy Watershed trực tiếp trong Fiji.},label={lst:groovy}]{code/ReplayWatershed.groovy}'
    if line=='@TEST_COMMANDS':return command('conda activate ai\ncd /d D:\\XU_LY_ANH\npython -B -m unittest discover -s tests -v\npython scripts/academic_smoke.py')
    if line=='@RUN_COMMANDS':return command('conda activate ai\ncd /d D:\\XU_LY_ANH\npython -m morpholab dataset synthetic\npython -m morpholab segment data\\synthetic\\synth_00.tif ^\n --truth data\\synthetic\\synth_00_gt.tif ^\n --out outputs\\demo_shared --fiji\npython scripts/academic_smoke.py')
    if line.startswith('@IMAGE '):
        path=ROOT/line[7:];name=path.name
        captions={'input_output.png':('Ảnh đầu vào, nhãn Python và nhãn Fiji: ví dụ bảy vật thể có hai cặp chạm nhau.','example'),'v2_compare_bbbc039_test':('F1 trung bình và khoảng tin cậy bootstrap 95% trên 50 ảnh test.','compare'),'v2_ablation_bbbc039':('Ablation: ảnh hưởng của từng bước trên 6 ảnh validation.','ablation'),'v2_robustness_bbbc039':('Robustness: biến đổi nhiễu/làm mờ trên cùng 6 ảnh validation.','robustness')}
        cap,label=captions.get(name,captions.get(path.parent.name,('Kết quả thực nghiệm.','result')))
        if name=='quality.png':name=path.parent.name+'.png'
        shutil.copyfile(path,OUT/'figures'/name)
        return fig(name,cap,label)
    if line=='@TOC':return ''
    raise ValueError(line)
def command(text):return '\n\n'+r'\par\medskip\noindent\begin{minipage}[t]{\linewidth}'+'\n'+r'\begin{lstlisting}[language={},numbers=none]'+'\n'+text+'\n'+r'\end{lstlisting}\end{minipage}\par\medskip'+'\n\n'
def content(title):
    lines=sections[title].splitlines();out=[];skip_caption=False
    for line in lines:
        if line.startswith('@'):
            if line.startswith('@IMAGE '):skip_caption=True
            out.append(directive(line))
        elif skip_caption and line.strip():skip_caption=False # caption is supplied explicitly
        else:
            if not line.strip():skip_caption=False
            out.append(esc(line))
    return '\n'.join(out)+'\n'
def section(title):return '\n'+r'\section{'+esc(title)+'}\n'+content(title)

preamble=r'''\documentclass[12pt,a4paper,oneside]{report}
\usepackage[margin=2.4cm,left=3cm,headheight=16pt]{geometry}
\usepackage{fontspec}
\IfFontExistsTF{Times New Roman}{\setmainfont{Times New Roman}}{\setmainfont{TeX Gyre Termes}}
\IfFontExistsTF{Arial}{\setsansfont{Arial}}{\setsansfont{TeX Gyre Heros}}
\IfFontExistsTF{Consolas}{\setmonofont{Consolas}}{\setmonofont{Latin Modern Mono}}
\usepackage{amsmath,amssymb,graphicx,booktabs,tabularx,array,float}
\usepackage{caption,subcaption,setspace,fancyhdr,titlesec,xcolor,listings,enumitem}
\usepackage[unicode,colorlinks=true,linkcolor=black,citecolor=black,urlcolor=blue,bookmarksnumbered=true]{hyperref}
\usepackage{bookmark}
\usepackage[section]{placeins}
\renewcommand{\contentsname}{Mục lục}
\renewcommand{\listfigurename}{Danh mục hình}
\renewcommand{\listtablename}{Danh mục bảng}
\renewcommand{\figurename}{Hình}
\renewcommand{\tablename}{Bảng}
\renewcommand{\chaptername}{Chương}
\renewcommand{\bibname}{Tài liệu tham khảo}
\renewcommand{\appendixname}{Phụ lục}
\renewcommand{\lstlistingname}{Mã nguồn}
\setcounter{tocdepth}{1}
\setlength{\parindent}{1.1cm}\setlength{\parskip}{4pt}
\setstretch{1.12}
\emergencystretch=2em
\pagestyle{fancy}\fancyhf{}
\fancyhead[L]{\small PTIT -- Xử lý ảnh}\fancyhead[R]{\small Nhóm 1}
\fancyfoot[C]{\thepage}\renewcommand{\headrulewidth}{0.4pt}
\fancypagestyle{plain}{\fancyhf{}\fancyfoot[C]{\thepage}\renewcommand{\headrulewidth}{0pt}}
\titleformat{\chapter}[display]{\bfseries\Large}{\chaptername\ \thechapter}{8pt}{\LARGE}
\titlespacing*{\chapter}{0pt}{0pt}{18pt}
\titleformat{\section}{\large\bfseries}{\thesection}{0.7em}{}
\captionsetup{font=small,labelfont=bf,labelsep=period}
\lstset{language=Python,basicstyle=\ttfamily\scriptsize,breaklines=true,breakatwhitespace=false,numbers=left,numberstyle=\tiny\color{gray},frame=single,rulecolor=\color{gray!40},columns=fullflexible,keepspaces=true,showstringspaces=false,tabsize=4,captionpos=b}
\hypersetup{pdftitle={Phân đoạn đối tượng bằng hình thái học toán học và Watershed},pdfauthor={PTIT Nhóm 1}}
\begin{document}\hypersetup{pageanchor=false}
\begin{titlepage}\centering
{\large\bfseries HỌC VIỆN CÔNG NGHỆ BƯU CHÍNH VIỄN THÔNG}\par
\vspace{1cm}{\large BÁO CÁO BÀI TẬP LỚN}\par
\vspace{0.3cm}{\Large\bfseries MÔN XỬ LÝ ẢNH}\par
\vspace{1.2cm}\rule{\linewidth}{0.6pt}\par
\vspace{0.5cm}{\LARGE\bfseries PHÂN ĐOẠN ĐỐI TƯỢNG BẰNG\par HÌNH THÁI HỌC TOÁN HỌC\par VÀ WATERSHED}\par
\vspace{0.5cm}\rule{\linewidth}{0.6pt}\par
\vspace{0.8cm}{\large Nền tảng tham chiếu: Fiji/ImageJ -- MorphoLibJ}\par
\vspace{0.7cm}{\large\bfseries Nhóm 1}\par\vspace{0.4cm}
\begin{tabular}{ll}\toprule
\textbf{Họ và tên}&\textbf{Mã sinh viên}\\\midrule
Kiều Trường Giang&B23DCCN254\\
Trần Đỗ Lan Phương&B23DCCN667\\
Giang Thùy Tiên&B23DCCN814\\
Phạm Văn Vỹ&B23DCCN954\\\bottomrule
\end{tabular}
\vfill
\href{https://github.com/jellalaz/XU_LY_ANH}{github.com/jellalaz/XU\_LY\_ANH}\par
\vspace{0.5cm}Tháng 11 năm 2026
\end{titlepage}
\pagenumbering{roman}\hypersetup{pageanchor=true}
\chapter*{Tóm tắt}\addcontentsline{toc}{chapter}{Tóm tắt}
'''
out=preamble+content('Tóm tắt và mục lục')
out+=r'\clearpage\tableofcontents\clearpage\listoffigures\clearpage\listoftables\clearpage\pagenumbering{arabic}'+'\n'
out+=r'\chapter{Giới thiệu và phạm vi nghiên cứu}\label{chap:intro}'+'\n'+section('Bài toán và câu hỏi nghiên cứu')
out+=r'\section{Mục tiêu và sản phẩm nghiên cứu}'+'\n'+esc('Nhóm cung cấp lý thuyết, mã tự cài, kết quả Fiji và đánh giá định lượng. MorphoLab hỗ trợ thao tác.')+'\n'
out+=r'\chapter{Cơ sở lý thuyết hình thái học và Watershed}\label{chap:theory}'+'\n'
for title in ['Biểu diễn ảnh và các quy ước toán học','Erosion và Dilation','Opening và Closing','Ví dụ tính tay và kết quả kiểm tra','Tái tạo hình thái','Gán nhãn các vùng liên thông','Biến đổi khoảng cách Euclid','Marker và lọc cực đại theo h','Watershed có điều khiển marker']:
    body=section(title)
    body=re.sub(r'\\lstinputlisting\[.*?\]\{.*?\}', '',body)
    out+=body
    if title=='Opening và Closing':out+=fig('morphology.png','Các toán tử hình thái chạy thật bằng Fiji native, SE vuông bán kính 1.','morphology')
out+=r'\chapter{Cài đặt và tổ chức quy trình Python}\label{chap:implementation}'+'\n'
for title in ['Quy trình Python hoàn chỉnh','Cài đặt reconstruction bằng hàng đợi','Tính khoảng cách bằng bao dưới của parabol','Mã cài đặt Watershed']:
    out+=section(title)
    if title=='Quy trình Python hoàn chỉnh':out+=fig('pipeline.png','Sáu bước trên cùng một ảnh: phân ngưỡng, làm sạch mask, khoảng cách, marker và nhãn.','pipeline')
out+=r'\chapter{Thực hành và kiểm chứng trên Fiji/ImageJ}\label{chap:fiji}'+'\n'
out+=section('Fiji và plugin MorphoLibJ')
out+=(OUT/'fiji_tutorial.tex').read_text(encoding='utf-8')
out+=section('Quy trình Fiji độc lập và các khác biệt')
out+=r'\chapter{Thiết kế thực nghiệm, kết quả và đánh giá}\label{chap:experiments}'+'\n'
for title in ['Dataset và nhãn đúng','Chỉ số định lượng và cách ghép đối tượng','Thiết kế thí nghiệm và kiểm soát sai lệch','Kết quả đối chiếu trên 50 ảnh test','Phân tích ảnh hưởng của từng bước','Ảnh hưởng của nhiễu và làm mờ','Benchmark và thực nghiệm tối ưu','Kiểm thử tính đúng và khả năng tái lập']:
    out+=section(title)
    if title=='Dataset và nhãn đúng':out+=fig('real_example.png','Ví dụ ảnh thật BBBC039, nhãn đúng và kết quả Python/Fiji native. Cùng ảnh test; màu ID chỉ hỗ trợ nhìn vùng.','real')
    if title=='Thiết kế thí nghiệm và kiểm soát sai lệch':out+=fig('ccl_watershed.png','Ví dụ có 7 vật thể: CCL trả 5 vùng, Watershed có marker trả 7. Không suy rộng từ một ảnh mẫu.','ccl')
out+=r'\chapter{Ứng dụng hỗ trợ, tái lập và kết luận}\label{chap:app}'+'\n'
out+=(OUT/'app.tex').read_text(encoding='utf-8')
for title in ['Hướng dẫn chạy phần nghiên cứu bằng lệnh','Kịch bản demo và kiểm tra trực tiếp','Giới hạn và kết luận']:out+=section(title)
out+=r'\clearpage\phantomsection\addcontentsline{toc}{chapter}{Tài liệu tham khảo}\begin{thebibliography}{9}'+'\n'
refs=sections['Tài liệu tham khảo'].split('\n\n')
for i,ref in enumerate(refs,1):
    # URLs in bibliography are clickable and breakable through hyperref.
    ref=re.sub(r'^\[\d+\]\s*','',ref).replace(' Tham khảo thông tin thư viện và bài giới thiệu, không tuyên bố đã đọc toàn văn bài báo.','')
    chunks=re.split(r'(https?://[^\s]+)',ref)
    formatted=''.join(r'\url{'+c.rstrip('.,')+'}' if c.startswith('http') else esc(c) for c in chunks)
    out+=r'\bibitem{ref'+str(i)+'} '+formatted+'\n\n'
out+=r'\end{thebibliography}\appendix\chapter{Kiểm tra hồ sơ và các lệnh tái lập}'+'\n'
out+=table(['Yêu cầu','Minh chứng'],[['Lý thuyết 8 nội dung','Chương 2, công thức đánh số, ví dụ tính tay'],['Tự cài thuật toán','Chương 3; mã nguồn Python trong repository'],['Thực hành Fiji','Chương 4, ảnh chụp thao tác và script Groovy'],['Định lượng hai nền tảng','Chương 5; CSV Python và Java/Fiji'],['Báo cáo và trình chiếu','Bản PDF LaTeX này và presentation 10 slide'],['App hỗ trợ','Chương 6, cùng phần lõi CLI']],'Đối chiếu các yêu cầu chính trong đề bài.','requirements')
out+=esc('Một đại diện nhóm nộp link theo LMS và ghi rõ Nhóm 1. Hạn trong đề là 19/11; nhóm xác nhận năm và giờ trên LMS. Nhóm kiểm tra tên, MSSV, phân công thực tế và luyện chạy lại demo. Hồ sơ chưa được nộp LMS tự động.')+'\n'
out+=r'\section{Mã script kiểm chứng trong Fiji}'+'\n'+directive('@FIJI_SCRIPT')
out+=r'\end{document}'
(OUT/'main.tex').write_text(out,encoding='utf-8')
print('LaTeX generated:',OUT/'main.tex')
