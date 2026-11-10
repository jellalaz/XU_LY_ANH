"""Lưu/nạp phiên thực nghiệm bằng TIFF/JSON, không dùng pickle hoặc mã thực thi."""
from dataclasses import dataclass
from pathlib import Path
import json
import numpy as np
import tifffile
from .io import export_result,read_image,read_labels,read_array,write_json
from .pipeline import Parameters,Result


@dataclass
class Session:
    image: np.ndarray
    result: Result
    truth: object = None
    reference: object = None
    source: object = None


def save_session(result,image,folder,truth=None,reference=None,source=None):
    """Lưu ảnh, cấu hình, nhãn đúng và kết quả để mở lại sau."""
    folder=Path(folder)
    if folder.exists() and any(folder.iterdir()):
        raise FileExistsError('Thư mục lưu phiên phải trống để không trộn kết quả cũ')
    folder=export_result(result,folder,source)
    tifffile.imwrite(folder/'input.tif',np.asarray(image))
    if truth is not None:
        from .io import validate_labels
        tifffile.imwrite(folder/'ground_truth.tif',validate_labels(truth,result.labels.shape))
    if reference is not None:
        from .io import validate_labels
        tifffile.imwrite(folder/'fiji_labels.tif',validate_labels(reference,result.labels.shape))
    data=json.loads((folder/'run.json').read_text(encoding='utf-8'))
    data.update(session_schema=1,stages=list(result.stages),has_truth=truth is not None,
                has_reference=reference is not None)
    write_json(folder/'run.json',data)
    if truth is not None:
        from .metrics import evaluate
        write_json(folder/'metrics.json',evaluate(truth,result.labels))
    if reference is not None:
        from .metrics import compare_labels
        write_json(folder/'fiji_comparison.json',compare_labels(reference,result.labels)[0])
    from .reporting import session_report
    session_report(folder)
    return folder


def _file(folder,name):
    folder=Path(folder).resolve(); path=(folder/name).resolve()
    if path.parent != folder: raise ValueError('Đường dẫn trong phiên làm việc không hợp lệ')
    return path


def load_session(folder):
    """Nạp phiên đã lưu và kiểm tra đường dẫn, kích thước, nhãn."""
    folder=Path(folder)
    data=json.loads(_file(folder,'run.json').read_text(encoding='utf-8'))
    if data.get('session_schema')!=1: raise ValueError('Chọn phiên đã lưu bằng chức năng Lưu phiên, không phải chỉ thư mục Fiji')
    p=Parameters(**data['parameters']).validate()
    image=read_image(_file(folder,'input.tif'))
    stages={}
    boolean={'binary','mask','morphology','erosion','dilation'}
    integer={'labels','components','markers','manual_markers'}
    required={'gray','mask','distance','elevation','markers','labels'}
    names=data.get('stages',[])
    if not required.issubset(names): raise ValueError('Phiên thiếu ảnh trung gian bắt buộc')
    if len(names)>30: raise ValueError('Phiên có quá nhiều ảnh trung gian')
    for name in names:
        if not isinstance(name,str) or not name.replace('_','').isalnum(): raise ValueError('Tên stage không hợp lệ')
        path=_file(folder,name+'.tif')
        a=read_labels(path,image.shape) if name in integer else read_array(path)
        if a.shape!=image.shape or not np.isfinite(a).all(): raise ValueError('Stage không cùng kích thước hoặc không hữu hạn')
        stages[name]=(a>0) if name in boolean else a
    result=Result(p,stages,float(data['threshold_normalized']),data['timings_seconds'])
    truth=read_labels(_file(folder,'ground_truth.tif'),image.shape) if data.get('has_truth') else None
    reference=read_labels(_file(folder,'fiji_labels.tif'),image.shape) if data.get('has_reference') else None
    return Session(image,result,truth,reference,data.get('source'))


def history(root='outputs'):
    """Liệt kê các phiên có dữ liệu để người dùng mở lại."""
    rows=[]
    for path in Path(root).glob('*/run.json'):
        try:
            data=json.loads(path.read_text(encoding='utf-8'))
            if data.get('session_schema')!=1: continue
            metrics={}
            if (path.parent/'metrics.json').exists(): metrics=json.loads((path.parent/'metrics.json').read_text(encoding='utf-8'))
            rows.append({'folder':str(path.parent.resolve()),'name':path.parent.name,'type':'session',
                'source':data.get('source'),'engine':data['parameters']['engine'],
                'mode':data['parameters']['mode'],'objects':data['objects'],
                'f1':metrics.get('object_f1'),'modified':path.stat().st_mtime})
        except (ValueError,KeyError,OSError): continue
    for path in Path(root).glob('*/study.json'):
        try:
            data=json.loads(path.read_text(encoding='utf-8'))
            rows.append({'folder':str(path.parent.resolve()),'name':path.parent.name,'type':'study',
                'mode':data['kind'],'engine':data['parameters']['engine'],
                'objects':data['planned_images'],'f1':None,'modified':path.stat().st_mtime})
        except (ValueError,KeyError,OSError): continue
    return sorted(rows,key=lambda r:r['modified'],reverse=True)
