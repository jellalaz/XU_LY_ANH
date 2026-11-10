"""Đọc, kiểm tra và xuất ảnh/nhãn. TIFF nhãn là dữ liệu đo, PNG màu chỉ để xem."""
from pathlib import Path
import json
import hashlib
import platform
import sys
from importlib.metadata import version
import numpy as np
import tifffile
from PIL import Image
from skimage import color, measure


def read_array(path):
    """Đọc TIFF bằng tifffile, các định dạng ảnh thông dụng khác bằng Pillow."""
    path = Path(path)
    return tifffile.imread(path) if path.suffix.lower() in ('.tif','.tiff') else np.asarray(Image.open(path))


def read_image(path):
    """Kiểm tra ảnh 2D hữu hạn; RGB/RGBA được chuyển về ảnh xám trước xử lý."""
    a = read_array(path)
    if a.ndim == 3 and a.shape[-1] in (3,4):
        a = color.rgb2gray(a[...,:3])
    if a.ndim != 2 or min(a.shape) < 3:
        raise ValueError('Chỉ hỗ trợ ảnh 2D hoặc RGB/RGBA. Hãy chọn một lát ảnh 3D.')
    if not np.isfinite(a).all():
        raise ValueError('Ảnh chứa NaN hoặc Infinity')
    if a.size > 16_000_000:
        raise ValueError('Ảnh quá lớn; hãy chọn ROI dưới 16 triệu pixel')
    return a


def validate_labels(a, shape=None):
    """Nhãn phải nguyên không âm, đúng kích thước; 0 là nền, ID dương là đối tượng."""
    a = np.asarray(a)
    if a.ndim != 2 or not np.isfinite(a).all() or np.any(a < 0) or np.any(a != np.floor(a)):
        raise ValueError('Nhãn phải là ảnh 2D số nguyên không âm; nền = 0')
    if shape is not None and a.shape != shape:
        raise ValueError(f'Kích thước nhãn {a.shape} khác ảnh {shape}; không tự resize ground truth')
    if a.max(initial=0) > np.iinfo(np.int32).max:
        raise ValueError('Nhãn vượt giới hạn int32')
    return a.astype(np.int32)


def read_labels(path, shape=None):
    """Đọc và kiểm tra ảnh nhãn, không tự co giãn nhãn để khớp kích thước."""
    return validate_labels(read_array(path), shape)


def normalized(a):
    """Chuẩn hóa min-max về [0,1]; ảnh hằng được ánh xạ thành 0."""
    a = np.asarray(a, float)
    lo, hi = float(a.min()), float(a.max())
    return (a-lo)/(hi-lo) if hi > lo else np.zeros_like(a)


def label_rgb(labels):
    """Tạo màu xác định từ ID để xem; ảnh TIFF nhãn gốc mới dùng tính điểm."""
    a = np.asarray(labels, np.uint64)
    rgb = np.stack([((a*67+53)%191)+64, ((a*97+17)%191)+64, ((a*137+29)%191)+64], -1).astype(np.uint8)
    rgb[a == 0] = 0
    return rgb


def overlay(gray, labels):
    """Chồng nhãn và biên lên ảnh xám để minh họa kết quả."""
    base = np.repeat(normalized(gray)[...,None],3,axis=2)
    rgb = label_rgb(labels)/255.
    valid = labels > 0
    base[valid] = .55*base[valid]+.45*rgb[valid]
    from skimage.segmentation import find_boundaries
    base[find_boundaries(labels, mode='inner')] = [0.25,1,0.8]
    return (np.clip(base,0,1)*255).astype(np.uint8)


def environment():
    """Ghi phiên bản Python, hệ điều hành và thư viện để tái lập."""
    return {'python':sys.version, 'platform':platform.platform(),
            'packages':{p:version(p) for p in ('numpy','scipy','scikit-image','matplotlib','tifffile')}}


def write_json(path, data):
    """Lưu JSON UTF-8 có dấu, không chấp nhận NaN/Infinity."""
    Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')


def object_table(labels, gray):
    """Đo diện tích, tâm, hộp bao và hình dạng của từng nhãn."""
    import pandas as pd
    properties = measure.regionprops_table(labels, intensity_image=normalized(gray),
        properties=('label','area','centroid','bbox','equivalent_diameter_area','eccentricity','solidity','intensity_mean'))
    return pd.DataFrame(properties)


def export_result(result, folder, source=None):
    """Xuất toàn bộ giai đoạn TIFF, ảnh màu, bảng đối tượng, tham số và thời gian."""
    folder = Path(folder)
    folder.mkdir(parents=True,exist_ok=True)
    for name, a in result.stages.items():
        a = np.asarray(a)
        if a.dtype == bool:
            a = a.astype(np.uint8)*255
        elif np.issubdtype(a.dtype,np.integer):
            a = a.astype(np.uint32)
        else:
            a = a.astype(np.float32)
        tifffile.imwrite(folder/f'{name}.tif',a,photometric='minisblack')
    Image.fromarray(overlay(result.stages['gray'],result.labels)).save(folder/'overlay.png')
    Image.fromarray(label_rgb(result.labels)).save(folder/'labels_rgb.png')
    object_table(result.labels,result.stages['gray']).to_csv(folder/'objects.csv',index=False,encoding='utf-8-sig')
    from dataclasses import asdict
    meta = {'parameters':asdict(result.params),'threshold_normalized':result.threshold,
            'timings_seconds':result.timings,'objects':int(np.unique(result.labels[result.labels>0]).size),
            'environment':environment(),'source':str(source) if source else None}
    if source and Path(source).is_file():
        meta['source_sha256'] = hashlib.sha256(Path(source).read_bytes()).hexdigest()
    write_json(folder/'run.json',meta)
    return folder
