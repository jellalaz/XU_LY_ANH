"""Kiểm tra log, số trang, trích mã rồi đóng gói PDF và nguồn LaTeX."""
from pathlib import Path
import ast
import hashlib
import json
import re
import shutil
import zipfile
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
build, source = ROOT/'outputs/latex_build', ROOT/'submission/latex'
tex = (source/'main.tex').read_text(encoding='utf-8')
for included in re.findall(r'\\input\{([^}]+)\}', tex):
    tex += '\n'+(source/(included+'.tex')).read_text(encoding='utf-8')
log = (build/'main.log').read_text(encoding='utf-8', errors='replace')
for error in ['Overfull \\hbox', 'Overfull \\vbox', 'Missing character:', 'undefined references', 'Undefined control sequence']:
    assert error not in log, error
pdf = PdfReader(build/'main.pdf')
assert not any('??' in p.extract_text() for p in pdf.pages)
labels = pdf.page_labels
arabic_start = next(i for i in range(2, len(labels)) if labels[i] == '1')
assert labels[1] == 'i'
assert labels[arabic_start:] == list(map(str, range(1, len(labels)-arabic_start+1)))
images = re.findall(r'\\includegraphics\[.*?\]\{(.*?)\}', tex)
assert all((source/name).is_file() for name in images)


def normalized(node):
    node = ast.parse(ast.unparse(node)).body[0]
    first = node.body[0]
    if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
        node.body.pop(0)
    return ast.dump(node, include_attributes=False)


tree = ast.parse((ROOT/'morpholab/algorithms.py').read_text(encoding='utf-8'))
for file in (source/'code').glob('*.py'):
    actual = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == file.stem)
    assert normalized(actual) == normalized(ast.parse(file.read_text(encoding='utf-8')).body[0]), file
dest = ROOT/'submission/BAO_CAO_NHOM_1.pdf'
shutil.copyfile(build/'main.pdf', dest)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
validation = dict(date='2026-11-10', engine='Tectonic / XeTeX', format='LaTeX',
    pdf_pages=len(pdf.pages), page_labels=labels, arabic_numbered_pages=len(labels)-arabic_start,
    figures=len(images), tables=tex.count('\\begin{table}'), equations=tex.count('\\begin{equation}'),
    unresolved_references=False, missing_glyphs=False, overfull_boxes=False,
    listing_executable_code_matches=True, pdf_sha256=sha(dest),
    manual_fiji_source='TIFF va anh chup thuc hanh nguoi hoc; docs/evidence/fiji_manual/verification.json')
(ROOT/'docs/evidence/academic_verification/latex_validation.json').write_text(json.dumps(validation, ensure_ascii=False, indent=2), encoding='utf-8')
with zipfile.ZipFile(ROOT/'submission/NGUON_LATEX_NHOM_1.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
    for file in sorted(source.rglob('*')):
        if file.is_file() and file.suffix in ('.tex', '.png', '.jpg', '.py', '.groovy', '.md'):
            archive.write(file, file.relative_to(source).as_posix())
manifest = dict(primary_report='BAO_CAO_NHOM_1.pdf', report_format='LaTeX',
    pdf_pages=len(pdf.pages), arabic_numbered_pages=len(labels)-arabic_start,
    slides=10, presentation_seconds=900, manual_fiji_evidence='docs/evidence/fiji_manual',
    report_order=['ly thuyet', 'Fiji lam tay', 'Python va doi chieu', 'thuc nghiem', 'app mo rong'], files={})
for name in ['BAO_CAO_NHOM_1.pdf', 'PRESENTATION_NHOM_1.pptx', 'NGUON_LATEX_NHOM_1.zip']:
    file = ROOT/'submission'/name
    if file.exists():
        manifest['files'][name] = dict(bytes=file.stat().st_size, sha256=sha(file))
(ROOT/'submission/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'PASS: {len(pdf.pages)} PDF pages, {len(labels)-arabic_start} numbered pages, {len(images)} figures; exact executable listings.')
