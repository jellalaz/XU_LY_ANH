"""Render LaTeX PDF and record printed page labels/links for final QA."""
from pathlib import Path
import json
import pypdfium2 as pdfium
from pypdf import PdfReader
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'outputs/latex_build/main.pdf';out=ROOT/'outputs/latex_review';out.mkdir(exist_ok=True)
reader=PdfReader(source);pdf=pdfium.PdfDocument(str(source))
pages=[]
for i,p in enumerate(pdf):
    p.render(scale=1.5).to_pil().save(out/f'page-{i+1:02}.png')
    text=reader.pages[i].extract_text()
    pages.append(dict(physical_page=i+1,printed_label=reader.page_labels[i],text=text))
for start in range(0,len(pdf),4):
    sheet=Image.new('RGB',(1200,1740),'#ddd');draw=ImageDraw.Draw(sheet)
    for j in range(4):
        if start+j>=len(pdf):break
        im=Image.open(out/f'page-{start+j+1:02}.png');im.thumbnail((590,835))
        x=(j%2)*600;y=(j//2)*870
        sheet.paste(im,(x,y+24));draw.text((x+8,y+5),f'PDF {start+j+1} / printed {reader.page_labels[start+j]}',fill='black')
    sheet.save(out/f'sheet-{start//4+1:02}.png')
assert not any('??' in p['text'] for p in pages),'Unresolved LaTeX reference'
assert any('Thực hành từng bước' in p['text'] for p in pages)
(out/'pages.json').write_text(json.dumps(pages,ensure_ascii=False,indent=2),encoding='utf-8')
print('Pages:',len(pdf),'labels:',reader.page_labels)
