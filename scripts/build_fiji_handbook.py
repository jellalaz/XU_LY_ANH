"""Typeset the full beginner Fiji lesson as a printable LaTeX handbook."""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'outputs/fiji_handbook';out.mkdir(exist_ok=True)
text=(ROOT/'submission/HUONG_DAN_FIJI_DAY_DU.md').read_text(encoding='utf-8')
def esc(s):
    repl={'\\':r'\textbackslash{}','&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','{':r'\{','}':r'\}','~':r'\textasciitilde{}','^':r'\textasciicircum{}','→':r'\ensuremath{\to}','≥':r'\ensuremath{\geq}','≤':r'\ensuremath{\leq}','×':r'\ensuremath{\times}','²':r'\ensuremath{^2}','σ':r'\ensuremath{\sigma}'}
    return ''.join(repl.get(c,c) for c in s)
def inline(s):
    tokens=re.split(r'(`[^`]+`|\*\*[^*]+\*\*|\[[^\]]+\]\([^)]+\))',s)
    parts=[]
    for t in tokens:
        if t.startswith('`') and t.endswith('`'):parts.append(r'\path{'+t[1:-1]+'}')
        elif t.startswith('**') and t.endswith('**'):parts.append(r'\textbf{'+esc(t[2:-2])+'}')
        elif re.match(r'^\[.+\]\(.+\)$',t):
            m=re.match(r'\[(.+)\]\((.+)\)',t);parts.append(r'\href{'+m[2]+'}{'+esc(m[1])+'}')
        else:parts.append(esc(t))
    return ''.join(parts)
head=r'''\documentclass[11pt,a4paper]{article}
\usepackage[margin=2.2cm,headheight=14pt]{geometry}
\usepackage{fontspec}
\setmainfont{Times New Roman}\setsansfont{Arial}\setmonofont{Consolas}
\usepackage{longtable,array,booktabs,graphicx,float,xcolor,listings,enumitem,fancyhdr}
\usepackage[unicode,colorlinks=true,linkcolor=black,urlcolor=blue,bookmarksnumbered]{hyperref}
\usepackage{bookmark}
\renewcommand{\contentsname}{Mục lục thực hành}
\renewcommand{\figurename}{Hình}
\setcounter{secnumdepth}{0}\setcounter{tocdepth}{1}
\setlength{\parindent}{0pt}\setlength{\parskip}{6pt}\emergencystretch=2em
\pagestyle{fancy}\fancyhf{}\fancyhead[L]{\small PTIT -- Nhóm 1}\fancyhead[R]{\small Bài thực hành Fiji}\fancyfoot[C]{\thepage}
\lstset{basicstyle=\ttfamily\scriptsize,breaklines=true,columns=fullflexible,keepspaces=true,showstringspaces=false,frame=single,rulecolor=\color{gray!50}}
\title{\sffamily\bfseries THỰC HÀNH FIJI ĐẦY ĐỦ\\\large Từ ảnh gốc đến phân đoạn và đánh giá}
\author{Xử lý ảnh -- PTIT Nhóm 1}\date{Tháng 11 năm 2026}
\begin{document}\maketitle
\tableofcontents\clearpage
'''
lines=text.splitlines();body=[];i=1
while i<len(lines):
    line=lines[i]
    if not line.strip():body.append('');i+=1;continue
    if line.startswith('```'):
        block=[];i+=1
        while i<len(lines) and not lines[i].startswith('```'):block.append(lines[i]);i+=1
        body.extend([r'\begin{lstlisting}','\n'.join(block),r'\end{lstlisting}']);i+=1;continue
    if line.startswith('|'):
        rows=[]
        while i<len(lines) and lines[i].startswith('|'):
            cells=[c.strip() for c in lines[i].strip().strip('|').split('|')]
            if not all(re.fullmatch(r'[:\-\s]+',c) for c in cells):rows.append(cells)
            i+=1
        n=len(rows[0]);widths=([.29,.65] if n==2 else [.23,.34,.35] if n==3 else [.94/n]*n)
        cols=''.join(r'>{\raggedright\arraybackslash}p{'+f'{w:.3f}'+r'\linewidth}' for w in widths)
        body.append(r'{\small\setlength{\tabcolsep}{3pt}\renewcommand{\arraystretch}{1.13}\begin{longtable}{'+cols+'}')
        header=' & '.join(r'\textbf{'+inline(c)+'}' for c in rows[0])+r' \\ \midrule'
        body.extend([r'\toprule',header,r'\endfirsthead\toprule',header,r'\endhead',r'\bottomrule\endfoot'])
        for row in rows[1:]:body.append(' & '.join(inline(c) for c in row)+r' \\')
        body.append(r'\end{longtable}}');continue
    if line.startswith('!['):
        m=re.match(r'!\[(.*?)\]\((.*?)\)',line)
        image=(ROOT/'submission'/m[2]).resolve().as_posix()
        body.append(r'\begin{figure}[H]\centering\includegraphics[width=\linewidth,height=0.48\textheight,keepaspectratio]{'+image+'}'+r'\caption{'+esc(m[1])+'}'+r'\end{figure}')
        i+=1;continue
    if line.startswith('### '):body.append(r'\subsection{'+inline(line[4:])+'}');i+=1;continue
    if line.startswith('## '):body.append(r'\section{'+inline(line[3:])+'}');i+=1;continue
    if line.startswith('- ') or re.match(r'^\d+\. ',line):
        numbered=bool(re.match(r'^\d+\. ',line));env='enumerate' if numbered else 'itemize'
        start=',start='+re.match(r'^(\d+)\.',line)[1] if numbered else ''
        body.append(r'\begin{'+env+r'}[leftmargin=*,itemsep=3pt'+start+']')
        while i<len(lines) and (re.match(r'^\d+\. ',lines[i]) if numbered else lines[i].startswith('- ')):
            value=re.sub(r'^\d+\. ','',lines[i]) if numbered else lines[i][2:]
            body.append(r'\item '+inline(value));i+=1
        body.append(r'\end{'+env+'}');continue
    if line.startswith('> '):body.append(r'\begin{quote}'+inline(line[2:])+r'\end{quote}');i+=1;continue
    body.append(inline(line));i+=1
(out/'handbook.tex').write_text(head+'\n'.join(body)+'\n'+r'\end{document}',encoding='utf-8')
print(out/'handbook.tex')
