"""Chạy lặp để đo tốc độ; tách rõ dữ liệu khảo sát và dữ liệu đánh giá cuối."""
from pathlib import Path
from dataclasses import replace, asdict
import json
import numpy as np
import pandas as pd
from .datasets import records
from .io import read_image,read_labels,write_json,environment
from .pipeline import run,Parameters
from .metrics import evaluate
from .tasks import check_cancelled,Cancelled


def process_folder(input_folder, output_folder, params=None, progress=print):
    """Chạy ảnh trong thư mục, tìm nhãn stem_gt.tif nếu có; không tự giả định luôn có nhãn đúng."""
    from .io import export_result
    source=Path(input_folder).resolve(); target=Path(output_folder).resolve()
    if source==target or source in target.parents:
        raise ValueError('Thư mục xuất phải nằm ngoài thư mục ảnh đầu vào')
    files=sorted(p for p in source.iterdir() if p.is_file() and p.suffix.lower() in ('.tif','.tiff','.png','.jpg','.jpeg','.bmp') and not p.stem.endswith('_gt'))
    if not files: raise ValueError('Thư mục không có ảnh hỗ trợ')
    target.mkdir(parents=True,exist_ok=True)
    rows=[]
    for i,path in enumerate(files):
        check_cancelled()
        # Thêm tiền tố để PNG/TIFF cùng tên gốc không ghi đè nhau.
        folder=target/f'{i:04d}_{path.stem}'
        try:
            image=read_image(path); result=run(image,params)
            export_result(result,folder,path)
            row={'image':path.name,'status':'ok','objects':int(result.labels.max(initial=0)),
                 'seconds':result.timings['total']}
            gt=next((source/(path.stem+'_gt'+s) for s in ('.tif','.tiff','.png') if (source/(path.stem+'_gt'+s)).exists()),None)
            if gt:
                metrics=evaluate(read_labels(gt,image.shape),result.labels)
                row.update(metrics); write_json(folder/'metrics.json',metrics)
            progress(f'{path.name}: {row["objects"]} đối tượng')
        except Cancelled: raise
        except Exception as exc:
            row={'image':path.name,'status':'error','error':str(exc)}
            progress(f'{path.name}: LỖI {exc}')
        rows.append(row)
        pd.DataFrame(rows).to_csv(target/'batch.csv',index=False,encoding='utf-8-sig')
    return pd.DataFrame(rows)


def benchmark(manifest, folder, params=None, split='validation', limit=None, repeats=3,
              engines=('custom','library'), modes=('ccl','raw','hmax','adaptive'), progress=print):
    """Đo nhiều lần sau làm nóng, không cộng đọc ghi/metric vào thời gian thuật toán Python."""
    if repeats<1: raise ValueError('Số lần đo phải >= 1')
    items=records(manifest,split,limit)
    if not items: raise ValueError('Không có ảnh trong split đã chọn')
    folder=Path(folder); folder.mkdir(parents=True,exist_ok=True)
    rows=[]
    for record,imagepath,truthpath in items:
        check_cancelled()
        image=read_image(imagepath); truth=read_labels(truthpath,image.shape)
        for engine in engines:
            for mode in modes:
                p=replace(params or Parameters(),engine=engine,mode=mode)
                # Không tính lượt làm nóng, đọc ghi và metric vào thời gian thuật toán.
                run(image,p)
                times=[]
                for repeat in range(repeats):
                    result=run(image,p); times.append(result.timings['total'])
                row={'image':record['id'],'split':split,'engine':engine,'mode':mode,
                    'seconds_median':float(np.median(times)),
                    'seconds_q25':float(np.quantile(times,.25)),'seconds_q75':float(np.quantile(times,.75)),
                    **evaluate(truth,result.labels)}
                rows.append(row)
                progress(f"{record['id'][:18]} · {engine}/{mode} · F1={row['object_f1']:.3f} · {row['seconds_median']:.3f}s")
                pd.DataFrame(rows).to_csv(folder/'per_image.csv',index=False,encoding='utf-8-sig')
    frame=pd.DataFrame(rows)
    summary=frame.groupby(['engine','mode'],as_index=False).agg(
        images=('image','count'),object_f1=('object_f1','mean'),foreground_iou=('foreground_iou','mean'),
        count_mae=('count_absolute_error','mean'),seconds_median=('seconds_median','median'),
        split_objects=('split_objects','sum'),merge_objects=('merge_objects','sum'))
    summary.to_csv(folder/'summary.csv',index=False,encoding='utf-8-sig')
    write_json(folder/'experiment.json',{'manifest':str(Path(manifest).resolve()),'split':split,
        'limit':limit,'repeats':repeats,'warmup':1,'parameters':asdict(params or Parameters()),
        'engines':list(engines),'modes':list(modes),'environment':environment(),
        'aggregation':'Macro mean metrics over images. Median runtime; IO and metrics excluded.',
        'warning':'Do not tune parameters using test split; adaptive is a hypothesis, not guaranteed improvement.'})
    # Xuất PNG biểu đồ cho báo cáo, không cần cửa sổ đồ họa.
    from matplotlib.figure import Figure
    fig=Figure(figsize=(11,4),layout='constrained')
    a,b=fig.subplots(1,2)
    for engine in summary.engine.unique():
        part=summary[summary.engine==engine]
        a.plot(part['mode'],part['object_f1'],'o-',label=engine)
        b.plot(part['mode'],part['seconds_median'],'o-',label=engine)
    a.set(title='Instance F1 (IoU >= 0.5)',ylim=(0,1.05),ylabel='Macro mean')
    b.set(title='Pipeline runtime',ylabel='Seconds (median)')
    a.legend(); b.legend(); a.grid(alpha=.2); b.grid(alpha=.2)
    fig.savefig(folder/'benchmark.png',dpi=160)
    return frame,summary


def sweep(manifest,folder,params=None,heights=(.5,1.,2.,4.,6.),limit=6,progress=print):
    """Khảo sát các mức h trên validation; không chọn tham số bằng nhãn test."""
    folder=Path(folder); folder.mkdir(parents=True,exist_ok=True)
    rows=[]
    base=replace(params or Parameters(),mode='hmax').validate()
    for height in heights:
        check_cancelled()
        _,summary=benchmark(manifest,folder/f'h_{height:g}',replace(base,h=float(height)),
            split='validation',limit=limit,repeats=1,engines=(base.engine,),modes=('hmax',),progress=progress)
        rows.append({'h':float(height),'object_f1':float(summary.object_f1.iloc[0])})
    table=pd.DataFrame(rows)
    best=table.sort_values(['object_f1','h'],ascending=[False,True]).iloc[0]
    write_json(folder/'selected_parameters.json',asdict(replace(base,h=float(best.h))))
    table.to_csv(folder/'sweep.csv',index=False)
    return table
