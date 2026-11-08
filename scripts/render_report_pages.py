from pathlib import Path
import pypdfium2 as pdfium
from PIL import Image,ImageDraw
root=Path(__file__).resolve().parents[1]/'outputs/report_qa'
pdf=pdfium.PdfDocument(str(root/'report.pdf'))
for i,page in enumerate(pdf):
    image=page.render(scale=1.5).to_pil();image.save(root/f'page-{i+1:02}.png')
for start in range(0,len(pdf),4):
    sheet=Image.new('RGB',(1200,1740),'#d0d0d0');draw=ImageDraw.Draw(sheet)
    for j in range(4):
        if start+j>=len(pdf):break
        im=Image.open(root/f'page-{start+j+1:02}.png');im.thumbnail((590,835))
        x=(j%2)*600;y=(j//2)*870
        sheet.paste(im,(x,y+22));draw.text((x+10,y+5),str(start+j+1),fill='black')
    sheet.save(root/f'sheet-{start//4+1}.png')
print('Rendered',len(pdf),'pages')
