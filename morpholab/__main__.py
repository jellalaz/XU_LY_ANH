import argparse
from pathlib import Path
import json
import sys
from .pipeline import Parameters,run
from .io import read_image,read_labels,export_result,write_json
from .datasets import synthetic,prepare_bbbc
from .metrics import evaluate


def main(argv=None):
    if hasattr(sys.stdout,'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description='MorphoLab PTIT · morphology + watershed + Fiji reference')
    sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('gui',help='Mở ứng dụng desktop')
    ds=sub.add_parser('dataset'); ds.add_argument('kind',choices=['synthetic','bbbc039']); ds.add_argument('--root',default='data')
    seg=sub.add_parser('segment'); seg.add_argument('image'); seg.add_argument('--truth'); seg.add_argument('--out',default='outputs/single')
    seg.add_argument('--fiji',action='store_true'); seg.add_argument('--fiji-home',default=r'C:\Tools\Fiji')
    seg.add_argument('--fiji-native',action='store_true',help='Independent native Fiji baseline')
    bench=sub.add_parser('benchmark'); bench.add_argument('manifest'); bench.add_argument('--out',default='outputs/benchmark')
    bench.add_argument('--split',choices=['training','validation','test'],default='validation'); bench.add_argument('--limit',type=int)
    bench.add_argument('--repeats',type=int,default=3); bench.add_argument('--engines',nargs='+',choices=['custom','library'],default=['custom','library'])
    bench.add_argument('--modes',nargs='+',choices=['ccl','raw','hmax','adaptive'],default=['ccl','raw','hmax','adaptive'])
    sw=sub.add_parser('sweep'); sw.add_argument('manifest'); sw.add_argument('--out',default='outputs/sweep'); sw.add_argument('--limit',type=int,default=6)
    batch=sub.add_parser('batch'); batch.add_argument('folder'); batch.add_argument('--out',default='outputs/batch')
    ev=sub.add_parser('evaluate'); ev.add_argument('truth'); ev.add_argument('prediction'); ev.add_argument('--out',default='outputs/metrics.json'); ev.add_argument('--iou',type=float,default=.5)
    for item in (seg,bench,sw,batch): item.add_argument('--config',default='configs/default.json')
    args=parser.parse_args(argv)
    if args.command=='gui':
        from .gui import launch
        launch(); return
    if args.command=='dataset':
        print(synthetic(args.root) if args.kind=='synthetic' else prepare_bbbc(args.root)); return
    if args.command=='evaluate':
        metrics=evaluate(read_labels(args.truth),read_labels(args.prediction),args.iou)
        Path(args.out).parent.mkdir(parents=True,exist_ok=True); write_json(args.out,metrics)
        print(json.dumps(metrics,indent=2)); return
    params=Parameters(**json.loads(Path(args.config).read_text(encoding='utf-8'))).validate()
    if args.command=='segment':
        image=read_image(args.image); result=run(image,params)
        out=export_result(result,args.out,args.image)
        truth=read_labels(args.truth,image.shape) if args.truth else None
        if truth is not None: write_json(out/'metrics.json',evaluate(truth,result.labels))
        if args.fiji or args.fiji_native:
            from .fiji import run_reference
            _,stats,_=run_reference(result,out/'fiji',truth,args.fiji_home,native=args.fiji_native)
            print(json.dumps(stats['comparison'],indent=2))
        print(f'{len(set(result.labels.ravel()))-int((result.labels==0).any())} objects; {result.timings["total"]:.3f}s; {out}')
    elif args.command=='benchmark':
        from .benchmark import benchmark
        _,summary=benchmark(args.manifest,args.out,params,args.split,args.limit,args.repeats,args.engines,args.modes)
        print(summary.to_string(index=False))
    elif args.command=='sweep':
        from .benchmark import sweep
        print(sweep(args.manifest,args.out,params,limit=args.limit).to_string(index=False))
    elif args.command=='batch':
        from .benchmark import process_folder
        frame=process_folder(args.folder,args.out,params)
        print(frame.to_string(index=False))
        if (frame.status=='error').any(): sys.exit(1)


if __name__=='__main__':
    try: main()
    except Exception as exc:
        print(f'ERROR: {exc}',file=sys.stderr)
        sys.exit(1)
