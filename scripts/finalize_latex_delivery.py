"""Validate and package the compiled LaTeX report; no algorithm changes."""
from pathlib import Path
import json,re,hashlib,shutil,zipfile,ast
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1]
build=ROOT/'outputs/latex_build';source=ROOT/'submission/latex'
tex=(source/'main.tex').read_text(encoding='utf-8')
log=(build/'main.log').read_text(encoding='utf-8',errors='replace')
for error in ['Overfull \\hbox','Overfull \\vbox','Missing character:','undefined references','Undefined control sequence']:
    assert error not in log,error
pdf=PdfReader(build/'main.pdf')
assert not any('??' in p.extract_text() for p in pdf.pages)
labels=pdf.page_labels
assert labels[1:6]==['i','ii','iii','iv','v']
assert labels[6:]==list(map(str,range(1,len(labels)-5)))
images=re.findall(r'\\includegraphics\[.*?\]\{(.*?)\}',tex)
assert all((source/name).is_file() for name in images)
assert len(images)==10
assert tex.count('\\begin{equation}')==17
# Confirm displayed executable code matches the real implementation, ignoring
# only docstrings/comments which are omitted in the report listings.
tree=ast.parse((ROOT/'morpholab/algorithms.py').read_text(encoding='utf-8'))
def normalized(n):
    n=ast.parse(ast.unparse(n)).body[0]
    if n.body and isinstance(n.body[0],ast.Expr) and isinstance(n.body[0].value,ast.Constant) and isinstance(n.body[0].value.value,str):n.body.pop(0)
    return ast.dump(n,include_attributes=False)
for file in (source/'code').glob('*.py'):
    expected=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==file.stem)
    assert normalized(expected)==normalized(ast.parse(file.read_text(encoding='utf-8')).body[0]),file
dest=ROOT/'submission/BAO_CAO_NHOM_1.pdf'
shutil.copyfile(build/'main.pdf',dest)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
validation={'date':'2026-11-09','engine':'Tectonic 0.17.0 / XeTeX','format':'LaTeX source compiled to PDF',
 'pdf_pages':len(pdf.pages),'page_labels':labels,'arabic_numbered_pages':len(labels)-6,
 'figures':len(images),'tables':tex.count('\\begin{table}'),'equations':tex.count('\\begin{equation}'),
 'unresolved_references':False,'missing_glyphs':False,'overfull_boxes':False,'listing_executable_code_matches':True,
 'pdf_sha256':sha(dest),'visual_review':'Rendered pages and reviewed layout, formulas, figures, tables, page numbering and commands.',
 'manual_fiji_ui':'Dialog field names verified against installed MorphoLibJ 1.6.5 plugin bytecode and manual; GUI images supplied by user in earlier practice.',
 'sources':{'MorphoLibJ':'https://imagej.net/plugins/morpholibj','Tectonic':'https://github.com/tectonic-typesetting/tectonic/releases/tag/tectonic@0.17.0'}}
(ROOT/'docs/evidence/academic_verification/latex_validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2),encoding='utf-8')
manifest_path=ROOT/'submission/manifest.json';manifest=json.loads(manifest_path.read_text())
manifest['BAO_CAO_NHOM_1.pdf']={'bytes':dest.stat().st_size,'sha256':sha(dest)}
manifest.update(pdf_pages=len(pdf.pages),arabic_numbered_pages=len(labels)-6,report_format='LaTeX',primary_report='BAO_CAO_NHOM_1.pdf',docx_status='Legacy before LaTeX additions; use PDF and latex/main.tex for final report.')
manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
delivery=ROOT/'outputs/delivery';delivery.mkdir(exist_ok=True)
archive=delivery/'BAO_CAO_LATEX_NHOM_1.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for file in sorted(source.rglob('*')):
        if file.is_file() and file.suffix not in ('.aux','.log','.toc','.lot','.lof','.xdv','.out') and file.name!='main.pdf':z.write(file,file.relative_to(source).as_posix())
with zipfile.ZipFile(archive) as z:assert z.testzip() is None;assert 'main.tex' in z.namelist()
print('PASS: PDF, LaTeX source ZIP, page labels, 10 figures, 17 equations, exact executable listings.')
print('Total PDF pages:',len(pdf.pages),'Arabic pages:',len(labels)-6,'Tables:',validation['tables'])
