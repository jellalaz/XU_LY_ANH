"""Kế hoạch đối chiếu, bỏ/thay từng bước và thử nhiễu/mờ, chạy tuần tự từng ảnh."""
from pathlib import Path
from dataclasses import replace,asdict
from datetime import datetime,timezone
from time import perf_counter
import json
import numpy as np
import pandas as pd
from scipy import ndimage as ndi
from PIL import Image
from .pipeline import Parameters,run
from .datasets import records
from .io import read_image,read_labels,write_json,environment,overlay,normalized
from .metrics import evaluate,compare_labels
from .tasks import check_cancelled,Cancelled


DESCRIPTIONS={
    'compare':'Đối chiếu Python tự cài, thư viện, Fiji dùng chung elevation/marker/mask và workflow Fiji độc lập.',
    'ablation':'Đo ảnh hưởng khi bỏ Gaussian, xử lý hình thái, reconstruction, lấp lỗ hoặc lọc marker; giữ nguyên dữ liệu.',
    'robustness':'Khảo sát nhiễu Gaussian và độ mờ có seed cố định; giữ nguyên nhãn hình học. Đây là stress test, không phải dữ liệu mới độc lập.'}


def _variants(kind,base,backends):
    """Tạo các cấu hình của cùng kế hoạch; mỗi biến thể ghi rõ thứ thay đổi."""
    if kind=='compare': return [(b,base,b,{}) for b in backends]
    if kind=='ablation':
        return [('baseline',base,'python',{}),('no_gaussian',replace(base,sigma=0),'python',{}),
            ('no_morphology',replace(base,operation='none'),'python',{}),
            ('ordinary_opening',replace(base,operation='opening'),'python',{}),
            ('no_fill_holes',replace(base,fill_holes=False),'python',{}),
            ('raw_markers',replace(base,mode='raw'),'python',{}),
            ('connected_components',replace(base,mode='ccl'),'python',{})]
    if kind=='robustness':
        return [('clean',base,'python',{}),
            *[(f'noise_{s:g}',base,'python',{'noise':s}) for s in (.02,.05,.1)],
            *[(f'blur_{s:g}',base,'python',{'blur':s}) for s in (1.,2.,3.)]]
    raise ValueError('Unknown study kind')


def _summary(rows):
    """Tổng hợp theo ảnh và bootstrap khoảng tin cậy với seed cố định."""
    frame=pd.DataFrame(rows)
    good=frame[frame.status=='ok'] if 'status' in frame else pd.DataFrame()
    output=[]
    if good.empty: return pd.DataFrame(columns=['variant','images','object_f1','ci_low','ci_high'])
    for name,part in good.groupby('variant',sort=False):
        scores=part.object_f1.to_numpy(float)
        rng=np.random.default_rng(20261108)
        means=scores[rng.integers(0,len(scores),size=(1000,len(scores)))].mean(1)
        row={'variant':name,'images':len(part),'object_f1':float(scores.mean()),
             'ci_low':float(np.quantile(means,.025)),'ci_high':float(np.quantile(means,.975)),
             'foreground_iou':float(part.foreground_iou.mean()),'count_mae':float(part.count_absolute_error.mean()),
             'split_objects':int(part.split_objects.sum()),'merge_objects':int(part.merge_objects.sum())}
        for key in ('pipeline_seconds','watershed_seconds','process_seconds','native_seconds_with_io','agreement'):
            if key in part and part[key].notna().any(): row[key]=float(part[key].dropna().median())
        output.append(row)
    return pd.DataFrame(output)


def _finish(folder,rows,meta):
    """Lưu CSV từng ảnh, tổng hợp, cấu hình, biểu đồ và phiếu HTML."""
    frame=pd.DataFrame(rows)
    frame.to_csv(folder/'per_image.csv',index=False,encoding='utf-8-sig')
    summary=_summary(rows)
    summary.to_csv(folder/'summary.csv',index=False,encoding='utf-8-sig')
    write_json(folder/'study.json',meta)
    from matplotlib.figure import Figure
    fig=Figure(figsize=(11,5),layout='constrained'); ax=fig.subplots()
    if len(summary):
        y=summary.object_f1.to_numpy(); x=np.arange(len(summary))
        ax.bar(x,y,color='#249e8a')
        # Khoảng tin cậy có thể bất đối xứng; chặn sai số âm do làm tròn.
        ax.errorbar(x,y,yerr=np.maximum(0,np.vstack([y-summary.ci_low,summary.ci_high-y])),fmt='none',ecolor='#172f43',capsize=4)
        ax.set_xticks(x,summary.variant,rotation=20,ha='right')
    ax.set(ylim=(0,1.05),ylabel='Macro instance F1 at IoU >= 0.5',title=meta['kind']+' / '+meta['split'])
    ax.grid(axis='y',alpha=.2); fig.savefig(folder/'quality.png',dpi=150)
    from .reporting import study_report
    study_report(folder)
    return frame,summary


def study(manifest,folder,params=None,kind='compare',split='validation',limit=6,repeats=2,
          backends=('python-custom','python-library','fiji-shared','fiji-native'),
          fiji_home=r'C:\Tools\Fiji',progress=print):
    """Chạy kế hoạch đối chiếu hoặc khảo sát trên split đã chọn; lưu từng dòng và không ghi đè đợt hoàn tất."""
    base=(params or Parameters()).validate()
    if kind not in DESCRIPTIONS: raise ValueError('Kế hoạch không hợp lệ')
    if not isinstance(repeats,int) or not 1<=repeats<=20: raise ValueError('Lặp đo [1,20]')
    allowed={'python-custom','python-library','fiji-shared','fiji-native'}
    if kind=='compare' and (not backends or not set(backends)<=allowed): raise ValueError('Backend không hợp lệ')
    if kind=='compare' and base.mode=='ccl' and 'fiji-shared' in backends:
        raise ValueError('Chọn hmax/raw/adaptive để đối chiếu Watershed; CCL không phải Watershed')
    items=records(manifest,split,limit)
    if not items: raise ValueError('Split không có ảnh')
    folder=Path(folder); folder.mkdir(parents=True,exist_ok=True)
    # Không trộn dữ liệu với đợt đã hoàn tất; cần thư mục đầu ra mới.
    if (folder/'study.json').exists(): raise FileExistsError('Thư mục đã có study; hãy chọn thư mục xuất mới')
    variants=_variants(kind,base,backends)
    rows=[]
    meta={'schema':1,'kind':kind,'description':DESCRIPTIONS[kind],'status':'running',
        'manifest':str(Path(manifest).resolve()),'split':split,'limit':limit,'repeats':repeats,
        'warmup_python':1,'parameters':asdict(base),'backends':list(backends),
        'planned_images':len(items),'seed':20261108,'started_utc':datetime.now(timezone.utc).isoformat(),
        'uncertainty':'Descriptive percentile bootstrap 95% CI of per-image mean F1, 1000 draws; not independent replicates across corrupted variants.',
        'timing':'Python pipeline excludes IO/metric. Shared Fiji watershed excludes JVM; process_seconds includes JVM and adapter. Native seconds includes intermediate TIFF writes. Sequential, one image at a time.',
        'environment':environment()}
    write_json(folder/'study.json',meta)
    try:
        for image_index,(record,imagepath,truthpath) in enumerate(items):
            check_cancelled()
            image=read_image(imagepath); truth=read_labels(truthpath,image.shape)
            shared=None
            for variant,p,backend,corruption in variants:
                check_cancelled()
                progress(f'{image_index+1}/{len(items)} · {record["id"][:20]} · {variant}')
                try:
                    observed=image
                    if corruption:
                        observed=normalized(image)
                        if 'noise' in corruption:
                            rng=np.random.default_rng(20261108+image_index)
                            observed=np.clip(observed+rng.normal(0,corruption['noise'],observed.shape),0,1)
                        else: observed=ndi.gaussian_filter(observed,corruption['blur'])
                    row={'image':record['id'],'split':split,'variant':variant,'status':'ok','backend':backend}
                    if backend in ('python','python-custom','python-library'):
                        engine=p.engine if backend=='python' else backend.split('-')[1]
                        cfg=replace(p,engine=engine)
                        run(observed,cfg)  # warm-up
                        times=[]; watershed_times=[]
                        for _ in range(repeats):
                            result=run(observed,cfg); times.append(result.timings['total'])
                            watershed_times.append(result.timings['watershed'])
                        labels=result.labels
                        row['pipeline_seconds']=float(np.median(times))
                        row['watershed_seconds']=float(np.median(watershed_times))
                    else:
                        from .fiji import run_reference
                        if shared is None: shared=run(image,base)
                        seconds=[]; process=[]
                        for repeat in range(repeats):
                            dest=folder/'fiji_runs'/record['id']/variant/str(repeat)
                            labels,stats,_=run_reference(shared,dest,truth,fiji_home,native=backend=='fiji-native')
                            independent=pd.read_csv(dest/'fiji_metrics.csv').iloc[0]
                            timing='watershed_seconds' if backend=='fiji-shared' else 'pipeline_seconds_including_intermediate_io'
                            seconds.append(float(independent[timing])); process.append(stats['process_seconds_including_jvm'])
                        row['watershed_seconds' if backend=='fiji-shared' else 'native_seconds_with_io']=float(np.median(seconds))
                        row['process_seconds']=float(np.median(process))
                        row['agreement']=compare_labels(shared.labels,labels)[0]['matched_pixel_agreement_foreground_union']
                    row.update(evaluate(truth,labels))
                    if image_index<3:
                        dest=folder/'gallery'/record['id']; dest.mkdir(parents=True,exist_ok=True)
                        Image.fromarray(overlay(observed,labels)).save(dest/(variant+'.png'))
                except Cancelled: raise
                except Exception as exc:
                    row={'image':record['id'],'split':split,'variant':variant,'backend':backend,'status':'error','error':str(exc)}
                    progress('LỖI: '+str(exc))
                rows.append(row)
                pd.DataFrame(rows).to_csv(folder/'per_image.csv',index=False,encoding='utf-8-sig')
        meta['status']='completed_with_errors' if any(r['status']=='error' for r in rows) else 'completed'
    except Cancelled:
        meta['status']='cancelled'
        if rows: _finish(folder,rows,meta)
        else: write_json(folder/'study.json',meta)
        raise
    meta['finished_utc']=datetime.now(timezone.utc).isoformat()
    return _finish(folder,rows,meta)
