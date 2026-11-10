"""Lưu và kiểm chứng các bước Fiji làm tay, tạo hình khoa học cho báo cáo.

Chạy lần đầu với --capture để lấy dữ liệu trong outputs/fiji_hoc_01.
Những lần sau đọc bản TIFF đã lưu ở docs/evidence/fiji_manual, không phụ
thuộc thư mục tạm hoặc phải chạy lại thao tác người học.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import shutil
import sys
import os

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('MPLCONFIGDIR', str(ROOT/'outputs/.matplotlib'))
import numpy as np
import tifffile
from scipy import ndimage as ndi
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from skimage.color import label2rgb
from morpholab.io import read_labels
from morpholab.metrics import evaluate, compare_labels
from morpholab.pipeline import Parameters, run

DEST = ROOT/'docs/evidence/fiji_manual'
FIG = ROOT/'submission/latex/figures'
FILES = {
    '01_input_8bit.tif': 'input_8bit.tif', '02_smooth.tif': 'smoothed.tif',
    '03_binary.tif': 'binary.tif', '04_erosion.tif': 'erosion.tif',
    '04_dilation.tif': 'dilation.tif', '05-Opening.tif': 'opening.tif',
    '06-Closing.tif': 'closing.tif', '07-seed.tif': 'seed.tif',
    '08-seed-rec.tif': 'reconstruction.tif', '10_mask.tif': 'mask.tif',
    '11_components.tif': 'components.tif', '12_distance.tif': 'distance.tif',
    '13_maxima_dung.tif': 'maxima.tif', '14_markers_dung.tif': 'markers.tif',
    '15_elevation.tif': 'elevation.tif', '16_watershed.tif': 'labels.tif',
    'GT_foreground.tif': 'gt_foreground.tif',
    'Prediction_foreground.tif': 'prediction_foreground.tif',
    'fiji_foreground_metrics.csv': 'fiji_foreground_metrics.csv',
}
# Đây là ảnh chụp do người học gửi, không phải giao diện mô phỏng.
SCREENS = {
    '3477fbe2-224b-44e9-b697-c01e71639128': 'ui_components.png',
    '63474bc0-a6a2-4bcf-ba41-f91f8a4f5827': 'ui_maxima.png',
    'c2d9b980-e2d6-48a9-add5-d0fd7a6cc442': 'ui_watershed.png',
    'e2f2b659-0791-462b-9f73-02b3521ccc34': 'ui_overlap.png',
}


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', action='store_true')
    args = parser.parse_args()
    DEST.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    if args.capture:
        for old, new in FILES.items():
            shutil.copyfile(ROOT/'outputs/fiji_hoc_01'/old, DEST/new)
        shutil.copyfile(ROOT/'data/synthetic/synth_00.tif', DEST/'input_16bit.tif')
        shutil.copyfile(ROOT/'data/synthetic/synth_00_gt.tif', DEST/'ground_truth.tif')
        for key, name in SCREENS.items():
            source = Path('C:/Users/Admin/AppData/Local/Temp')/f'codex-clipboard-{key}.png'
            if source.exists():
                shutil.copyfile(source, DEST/name)

    def read(name):
        return tifffile.imread(DEST/(name+'.tif'))

    truth, labels = read_labels(DEST/'ground_truth.tif'), read_labels(DEST/'labels.tif')
    measured = evaluate(truth, labels)
    # Kiểm tra hai mask dùng đo trong Fiji có thật sự là nhị phân từ ID dương.
    assert set(np.unique(read('gt_foreground'))) <= {0, 255}
    assert set(np.unique(read('prediction_foreground'))) <= {0, 255}
    assert np.array_equal(read('gt_foreground') > 0, truth > 0)
    assert np.array_equal(read('prediction_foreground') > 0, labels > 0)
    with (DEST/'fiji_foreground_metrics.csv').open(encoding='utf-8-sig') as handle:
        fiji = next(csv.DictReader(handle))
    assert abs(float(fiji['JaccardIndex'])-measured['foreground_iou']) < 1e-6
    assert abs(float(fiji['DiceCoefficient'])-measured['foreground_dice']) < 1e-6
    assert len(np.unique(labels[labels > 0])) == 7
    assert len(np.unique(read('components')[read('components') > 0])) == 5
    assert len(np.unique(read('markers')[read('markers') > 0])) == 7
    # File người học lưu trước phép nhân còn là distance dương. Giữ bản gốc
    # để truy vết, rồi xuất lại đúng E=-D. Nhãn cuối không bị sửa hay vẽ lại.
    if np.array_equal(read('elevation'), read('distance')):
        shutil.copyfile(DEST/'elevation.tif', DEST/'elevation_saved_before_multiply.tif')
        tifffile.imwrite(DEST/'elevation.tif', -read('distance'), imagej=True)
    assert np.allclose(read('elevation'), -read('distance'))
    assert np.all(labels[read('mask') == 0] == 0)
    binary = read('binary') > 0
    matched_radii = {}
    for key, method in [('erosion', ndi.binary_erosion), ('dilation', ndi.binary_dilation),
                        ('opening', ndi.binary_opening), ('closing', ndi.binary_closing),
                        ('seed', ndi.binary_erosion)]:
        matched_radii[key] = [r for r in range(1, 6) if np.array_equal(
            read(key) > 0, method(binary, structure=np.ones((2*r+1, 2*r+1)), border_value=0))]
    result = run(read('input_16bit'), Parameters())
    python_metrics = evaluate(truth, result.labels)
    agreement, _ = compare_labels(labels, result.labels)
    metadata = {
        'source': 'TIFF người học tự lưu từ thao tác menu Fiji trong buổi thực hành',
        'input': 'synth_00.tif, 192 x 192, một kênh 16-bit',
        'step_parameters': {'sigma': 1, 'threshold': 'Otsu trên ảnh 8-bit',
            'element': 'Square', 'h': 2, 'connectivity': 4, 'min_area': 25,
            'dams': False, 'compactness': 0},
        'radius_matches_by_array': matched_radii,
        'elevation_correction': 'Giữ nguyên file dương đã lưu dưới tên elevation_saved_before_multiply.tif; xuất lại elevation=-distance. Chạy lại MorphoLibJ với địa hình âm khớp nhãn làm tay sau ghép ID: không pixel bất đồng; địa hình dương lệch 1915 pixel.',
        'parameter_scope': 'Thông số theo nhật ký hội thoại; bán kính còn được kiểm tra bằng mảng TIFF, không suy đoán từ tên ảnh.',
        'fiji_gui_csv': fiji, 'python_evaluation_of_manual_fiji': measured,
        'python_default_metrics': python_metrics, 'manual_fiji_vs_python': agreement,
        'checks': '5 thành phần, 7 marker, 7 nhãn; elevation=-distance; mask foreground và CSV GUI khớp Python',
        'sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(DEST.glob('*')) if p.suffix in ('.tif', '.png', '.csv')},
    }
    (DEST/'verification.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10})

    def panel(filename, keys, titles, modes=None, cols=3):
        modes = modes or {}
        rows = (len(keys)+cols-1)//cols
        fig, axes = plt.subplots(rows, cols, figsize=(11, 3.35*rows), squeeze=False)
        for i, (key, title) in enumerate(zip(keys, titles)):
            a = read(key)
            ax = axes.flat[i]
            mode = modes.get(key)
            if mode == 'label':
                ax.imshow(label2rgb(a.astype(int), bg_label=0), interpolation='nearest')
            else:
                im = ax.imshow(a, cmap='magma' if mode == 'distance' else 'gray', interpolation='nearest')
                if mode in ('distance', 'elevation'):
                    fig.colorbar(im, ax=ax, fraction=.046, pad=.04)
            if mode == 'marker':
                # Chỉ khoanh chú giải vị trí; ảnh TIFF giữ nguyên kích thước marker.
                for marker in np.unique(a[a > 0]):
                    yy, xx = np.nonzero(a == marker)
                    ax.plot(xx.mean(), yy.mean(), 'o', ms=15, mfc='none', mec='cyan')
                    ax.text(xx.mean()+7, yy.mean(), str(int(marker)), color='cyan', fontsize=10)
            ax.set_title(title, pad=8)
            ax.axis('off')
        for ax in axes.flat[len(keys):]:
            ax.axis('off')
        fig.tight_layout()
        fig.savefig(FIG/filename, dpi=180, bbox_inches='tight')
        plt.close(fig)

    panel('manual_preprocess.png', ['input_16bit', 'input_8bit', 'smoothed', 'binary'],
          ['(a) Gốc 16-bit', '(b) Bản sao 8-bit', '(c) Gaussian, sigma = 1', '(d) Otsu và Apply'], cols=4)
    panel('manual_morphology.png', ['binary', 'erosion', 'dilation', 'opening', 'closing', 'reconstruction'],
          ['(a) Nhị phân gốc', '(b) Co: Square r=1', '(c) Giãn: Square r=3', '(d) Mở: Square r=2', '(e) Đóng: Square r=2', '(f) Tái tạo từ seed co r=4'])
    panel('manual_watershed.png', ['mask', 'components', 'distance', 'markers', 'elevation', 'labels'],
          ['(a) Mask sạch', '(b) Liên thông: 5 nhãn', '(c) Khoảng cách tới nền', '(d) 7 marker (vòng chú giải)', '(e) Địa hình = -distance', '(f) Watershed: 7 nhãn'],
          {'components': 'label', 'distance': 'distance', 'markers': 'marker', 'elevation': 'elevation', 'labels': 'label'})
    panel('manual_evaluation.png', ['ground_truth', 'labels', 'gt_foreground', 'prediction_foreground'],
          ['(a) Nhãn đúng 1–7', '(b) Nhãn Fiji 1–7', '(c) Mask nhãn đúng > 0', '(d) Mask dự đoán > 0'],
          {'ground_truth': 'label', 'labels': 'label'}, cols=4)
    for name in SCREENS.values():
        if (DEST/name).exists():
            shutil.copyfile(DEST/name, FIG/name)
    print(json.dumps({k: v for k, v in metadata.items() if k != 'sha256'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
