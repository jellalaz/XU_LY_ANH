"""Legacy Word-to-PDF layout. The primary report now lives in submission/latex."""
from pathlib import Path
from xml.sax.saxutils import escape
from docx import Document
from docx.oxml.ns import qn
from docx.table import Table as DocxTable
from docx.text.paragraph import Paragraph as DocxParagraph
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate,Paragraph,Table,TableStyle,PageBreak,Spacer,Image,Preformatted,KeepTogether
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor,black
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
import io,json,re

ROOT=Path(__file__).resolve().parents[1]
dest=ROOT/'outputs/BAO_CAO_NHOM_1_WORD_LEGACY.pdf'
for name,file in [('TimesVN','times.ttf'),('TimesVNBold','timesbd.ttf'),('ArialVN','arial.ttf'),('ArialVNBold','arialbd.ttf'),('Code','consola.ttf'),('Math','seguisym.ttf')]:
    pdfmetrics.registerFont(TTFont(name,'C:/Windows/Fonts/'+file))
normal=ParagraphStyle('body',fontName='TimesVN',fontSize=11.5,leading=15,spaceAfter=7,textColor=black)
heading=ParagraphStyle('heading',fontName='ArialVNBold',fontSize=16,leading=21,spaceAfter=14)
cover=ParagraphStyle('cover',parent=heading,fontSize=23,leading=29,spaceAfter=19)
caption=ParagraphStyle('caption',fontName='TimesVNBold',fontSize=9,leading=11,spaceAfter=8)
small=ParagraphStyle('small',parent=normal,fontSize=9.5,leading=12,spaceAfter=3)
cell=ParagraphStyle('cell',parent=normal,fontSize=9,leading=11,spaceAfter=0)
cellhead=ParagraphStyle('cellhead',parent=cell,fontName='TimesVNBold')
formula=ParagraphStyle('formula',fontName='TimesVN',fontSize=11,leading=16,alignment=TA_CENTER,spaceAfter=8)
code=ParagraphStyle('code',fontName='Code',fontSize=7.2,leading=8.4,spaceAfter=8)
doc=Document(ROOT/'submission/BAO_CAO_NHOM_1.docx')
story=[]; page=1; W=A4[0]-57-57
def txt(el):
    return ''.join(n.text or '' for n in el.iter() if n.tag in (qn('w:t'),'{http://schemas.openxmlformats.org/officeDocument/2006/math}t'))
def paragraph(text,style):
    if style is formula:
        # The symbol font lacks Vietnamese letters. Use it only for glyphs
        # absent from Times, preserving searchable Unicode in both fonts.
        coverage=pdfmetrics.getFont('TimesVN').face.charWidths
        markup=''.join(escape(ch) if ord(ch) in coverage else '<font name="Math">'+escape(ch)+'</font>' for ch in text)
        return Paragraph(markup,style)
    return Paragraph(escape(text).replace('\n','<br/>'),style)
for el in doc.element.body:
    if el.tag==qn('w:p'):
        if any(b.get(qn('w:type'))=='page' for b in el.iter(qn('w:br'))):story.append(PageBreak());page+=1;continue
        p=DocxParagraph(el,doc)
        drawings=list(el.iter(qn('a:blip')))
        if drawings:
            for b in drawings:
                blob=doc.part.related_parts[b.get(qn('r:embed'))].blob
                im=Image(io.BytesIO(blob));im.drawHeight*=W/im.drawWidth;im.drawWidth=W
                story.append(im);story.append(Spacer(1,5))
            continue
        text=p.text if p.text else txt(el)
        if not text:continue
        if list(el.iter('{http://schemas.openxmlformats.org/officeDocument/2006/math}oMath')):story.append(paragraph(txt(el),formula));continue
        if p.runs and p.runs[0].font.name=='Consolas':
            story.append(Preformatted(text,code,maxLineLength=113));continue
        style=cover if p.style.name=='Title' else heading if p.style.name.startswith('Heading') else caption if p.style.name=='Caption' else small if p.runs and p.runs[0].font.size and p.runs[0].font.size.pt<=10 else normal
        story.append(paragraph(text,style))
    elif el.tag==qn('w:tbl'):
        t=DocxTable(el,doc);values=[]
        for ri,row in enumerate(t.rows):values.append([paragraph(c.text,cellhead if ri==0 else cell) for c in row.cells])
        cols=len(values[0]); widths=[W/cols]*cols
        if cols==6:widths=[100,31,49,99,52,W-331]
        if cols==2:widths=[W*.43,W*.57]
        table=Table(values,colWidths=widths,repeatRows=1,hAlign='LEFT')
        table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),HexColor('#E6EDF2')),('ROWBACKGROUNDS',(0,1),(-1,-1),[HexColor('#F5F7F9'),HexColor('#FFFFFF')]),('GRID',(0,0),(-1,-1),.35,HexColor('#D4DADF')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
        story.append(table);story.append(Spacer(1,8))
def page_canvas(c,d):
    c.saveState();c.setFillColor(black);c.setFont('TimesVNBold',9)
    c.drawString(57,A4[1]-34,'PTIT  •  Xử lý ảnh  •  Nhóm 1')
    c.setFont('TimesVN',10);c.drawRightString(A4[0]-57,30,f'Nhóm 1   |   {d.page}');c.restoreState()
pdf=SimpleDocTemplate(str(dest),pagesize=A4,leftMargin=57,rightMargin=57,topMargin=58,bottomMargin=49,title='Phân đoạn đối tượng bằng hình thái học toán học và Watershed',author='PTIT Nhóm 1')
pdf.build(story,onFirstPage=page_canvas,onLaterPages=page_canvas)
print(dest)
