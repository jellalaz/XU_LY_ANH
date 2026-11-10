"""Biên dịch báo cáo chính từ LaTeX; không tạo lại bản Word cũ.

Ví dụ: python scripts/build_report.py --tectonic C:/Tools/tectonic.exe
Nếu không truyền đường dẫn, tìm tectonic trên PATH hoặc outputs/tools/tectonic.
Chỉ cập nhật trích mã và biên dịch main.tex; không ghi đè nội dung đã biên tập.
"""
from pathlib import Path
import argparse
import ast
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tectonic')
    args = parser.parse_args()
    source = ROOT/'submission/latex'
    build = ROOT/'outputs/latex_build'
    build.mkdir(parents=True, exist_ok=True)
    code = (ROOT/'morpholab/algorithms.py').read_text(encoding='utf-8')
    for node in ast.parse(code).body:
        if isinstance(node, ast.FunctionDef) and node.name in (
                'reconstruction_dilation', 'connected_components', '_squared_edt_1d', 'watershed'):
            # Bản trích giữ nguyên câu lệnh; bỏ docstring/comment để listings gọn.
            lines = ast.get_source_segment(code, node).splitlines()
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                del lines[first.lineno-node.lineno:first.end_lineno-node.lineno+1]
            text = '\n'.join(line for line in lines if line.strip() and not line.lstrip().startswith('#'))
            (source/'code'/(node.name+'.py')).write_text(text+'\n', encoding='utf-8')
    groovy = (ROOT/'fiji/ReplayWatershed.groovy').read_text(encoding='utf-8')
    groovy = '\n'.join(line for line in groovy.splitlines() if not line.lstrip().startswith('//'))
    (source/'code/ReplayWatershed.groovy').write_text(groovy+'\n', encoding='utf-8')
    exe = args.tectonic or shutil.which('tectonic')
    if not exe:
        candidate = ROOT/'outputs/tools/tectonic/tectonic.exe'
        if candidate.exists():
            exe = str(candidate)
    if not exe:
        raise SystemExit('Chua tim thay Tectonic. Dung XeLaTeX/Overleaf hoac truyen --tectonic.')
    with (build/'console.txt').open('w', encoding='utf-8') as output:
        proc = subprocess.run([exe, '-k', '--keep-logs', '--outdir', str(build), str(source/'main.tex')],
                              stdout=output, stderr=subprocess.STDOUT)
    if proc.returncode:
        raise SystemExit('LaTeX build failed: outputs/latex_build/console.txt')
    subprocess.run([sys.executable, str(ROOT/'scripts/finalize_latex_delivery.py')], check=True)
    print('PASS: submission/BAO_CAO_NHOM_1.pdf')


if __name__ == '__main__':
    main()
