"""Chạy lại ví dụ báo cáo, tạo trang xem kết quả, không cần pandas.

Dùng cùng thuật toán, cấu hình và adapter Fiji như báo cáo.
HTML chỉ để xem; kiểm chứng số dựa trên TIFF nhãn.
"""
import argparse
import csv
from dataclasses import replace
import html
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
from PIL import Image
import tifffile

from morpholab.datasets import records
from morpholab.fiji import run_reference
from morpholab.io import normalized, overlay, read_image, read_labels, write_json
from morpholab.metrics import evaluate
from morpholab.pipeline import Parameters, run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--limit', type=int, default=3)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    if not 1 <= args.limit <= 50:
        parser.error('--limit must be between 1 and 50')
    folder = Path(args.out).resolve()
    if folder.exists() and any(folder.iterdir()):
        parser.error('Choose a new or empty output folder')
    folder.mkdir(parents=True, exist_ok=True)
    params = Parameters(**json.loads((ROOT/'configs/default.json').read_text(encoding='utf-8')))
    baseline_path = ROOT/'docs/evidence/v2_compare_bbbc039_test/per_image.csv'
    with baseline_path.open(encoding='utf-8-sig', newline='') as handle:
        old = {(r['image'], r['variant']): r for r in csv.DictReader(handle)}
    rows, sections = [], []
    variants = ('python-custom', 'python-library', 'fiji-shared', 'fiji-native')
    for index, (record, source, gtpath) in enumerate(records(ROOT/'data/bbbc039/manifest.json', 'test', args.limit), 1):
        name = record['id']
        dest = folder/name
        dest.mkdir()
        image = read_image(source)
        truth = read_labels(gtpath, image.shape)
        Image.fromarray((normalized(image)*255).astype(np.uint8)).save(dest/'input.png')
        Image.fromarray(overlay(image, truth)).save(dest/'ground_truth.png')
        shared = None
        tiles = [('Ảnh gốc', 'input.png'), ('Nhãn đúng', 'ground_truth.png')]
        for variant in variants:
            print(f'{index}/{args.limit} {variant}: {name}', flush=True)
            if variant.startswith('python-'):
                result = run(image, replace(params, engine=variant.split('-')[1]))
                labels = result.labels
                if variant == 'python-custom':
                    shared = result
            else:
                labels, _, _ = run_reference(shared, dest/variant, truth, native=variant == 'fiji-native')
            metric = evaluate(truth, labels)
            expected = old[(name, variant)]
            keys = ('foreground_iou', 'foreground_dice', 'object_f1', 'true_objects', 'predicted_objects')
            matched = all(np.isclose(metric[k], float(expected[k]), rtol=0, atol=1e-9) for k in keys)
            row = {'image': name, 'variant': variant, 'matches_report': bool(matched), **metric}
            rows.append(row)
            write_json(dest/(variant+'_metrics.json'), metric)
            tifffile.imwrite(dest/(variant+'_labels.tif'), labels.astype(np.uint32))
            Image.fromarray(overlay(image, labels)).save(dest/(variant+'.png'))
            tiles.append((f"{variant}: {metric['predicted_objects']} vật; F1={metric['object_f1']:.4f}", variant+'.png'))
            print(f"  {'PASS' if matched else 'MISMATCH'} report; truth={metric['true_objects']}, predicted={metric['predicted_objects']}, F1={metric['object_f1']:.4f}", flush=True)
        cards = ''.join(f'<figure><img src="{html.escape(name)}/{file}"><figcaption>{html.escape(title)}</figcaption></figure>' for title, file in tiles)
        sections.append(f'<h2>Ảnh {index}: {html.escape(name)}</h2><p>Nhãn đúng: {metric["true_objects"]} đối tượng. Ảnh gốc: {html.escape(str(source))}</p><div class="grid">{cards}</div>')
    with (folder/'check.csv').open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    passed = all(row['matches_report'] for row in rows)
    write_json(folder/'verification.json', {'all_match_report': passed, 'images': args.limit, 'rows': len(rows), 'baseline': str(baseline_path), 'metric_tolerance': 1e-9, 'parameters': json.loads((ROOT/'configs/default.json').read_text()), 'scope': 'Numeric replay of first test images; not an independent new dataset or a test of timing.'})
    document = '''<!doctype html><html lang="vi"><meta charset="utf-8"><title>Kiểm chứng báo cáo — ảnh thật</title><style>body{font:16px Arial;margin:24px;background:#f2f5f8;color:#163149}h2{margin-top:40px;overflow-wrap:anywhere}.grid{display:grid;grid-template-columns:repeat(3,minmax(200px,1fr));gap:16px}figure{margin:0;background:white;padding:12px;border-radius:10px}img{width:100%;height:auto}figcaption{padding-top:10px}p{overflow-wrap:anywhere}@media(max-width:800px){.grid{grid-template-columns:1fr}}</style><h1>Kiểm chứng báo cáo trên ảnh thật</h1>'''
    document += f'<p>Đối chiếu {len(rows)} kết quả với CSV đã dùng trong báo cáo: <b>{"PASS" if passed else "MISMATCH"}</b>. F1 thấp là kết quả nghiên cứu, không đồng nghĩa chương trình bị lỗi.</p>'
    document += '<p>Ảnh màu là minh họa. TIFF nhãn và các JSON/CSV trong cùng thư mục là dữ liệu để kiểm tra. Nhãn đúng chỉ dùng đánh giá.</p>'
    document += ''.join(sections)+'</html>'
    (folder/'index.html').write_text(document, encoding='utf-8')
    print(f"{'ALL REPORT VALUES MATCH' if passed else 'REPORT MISMATCH'}: {folder/'index.html'}", flush=True)
    if not passed:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
