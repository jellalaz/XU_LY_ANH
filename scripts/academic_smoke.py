"""Reproduce a small, assertable Python/Fiji demonstration without the GUI."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import argparse
import csv
import json
from datetime import datetime
from dataclasses import replace
import numpy as np
from morpholab.datasets import synthetic
from morpholab.pipeline import Parameters, run
from morpholab.io import read_image, read_labels, export_result, write_json
from morpholab.metrics import evaluate
from morpholab.fiji import run_reference, installation, _execute


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', default=str(ROOT/'outputs'/('academic_smoke_'+datetime.now().strftime('%Y%m%d_%H%M%S'))))
    parser.add_argument('--fiji-home', default=r'C:\Tools\Fiji')
    args = parser.parse_args()
    out = Path(args.out).resolve()
    if out.exists() and any(out.iterdir()):
        raise ValueError('Choose a new output folder; existing results are preserved.')
    out.mkdir(parents=True, exist_ok=True)
    source = ROOT/'data/synthetic/synth_00.tif'
    if not source.exists(): synthetic(ROOT/'data')
    truth = read_labels(source.with_name('synth_00_gt.tif'))
    image = read_image(source)
    params = Parameters(**json.loads((ROOT/'configs/default.json').read_text(encoding='utf-8')))
    summary = []
    base = None
    for name, settings, expected in [('hmax',params,7),('ccl',replace(params,mode='ccl'),5),('empty',replace(params,min_area=100000),0)]:
        result = run(image,settings)
        export_result(result,out/name,source)
        score = evaluate(truth,result.labels)
        write_json(out/name/'metrics.json',score)
        assert score['predicted_objects']==expected,(name,score)
        if name=='hmax':
            assert score['object_f1']==1
            base=result
        if name=='empty': assert score['object_f1']==0
        summary.append({'case':name,**score})
        print(f"PASS {name}: objects={expected}, F1={score['object_f1']:.4f}",flush=True)
    for native in (False,True):
        name='fiji_native' if native else 'fiji_shared'
        labels,stats,_=run_reference(base,out/name,truth,args.fiji_home,native=native)
        score=evaluate(truth,labels)
        with (out/name/'fiji_metrics.csv').open(encoding='utf-8-sig') as f: java=next(csv.DictReader(f))
        for key in ('foreground_iou','foreground_dice'):
            assert np.isclose(float(java[key]),score[key],rtol=0,atol=1e-10),(name,key)
        assert int(java['predicted_objects'])==score['predicted_objects']
        summary.append({'case':name,**score})
        print(f"PASS {name}: Java/Python metrics agree; objects={score['predicted_objects']}, F1={score['object_f1']:.4f}",flush=True)
    # Execute the actual reusable Groovy script with equivalent SciJava bindings.
    # Only its optional image display is disabled, so this can run headlessly.
    java,*_=installation(args.fiji_home)
    runner=out/'check_replay.groovy'
    runner.write_text('''def source = new File('''+json.dumps((ROOT/'fiji/ReplayWatershed.groovy').as_posix())+''')
def binding = new Binding([folder:new File('''+json.dumps((out/'fiji_shared').as_posix())+'''), connectivity:4, showImages:false])
new GroovyShell(binding).evaluate(source.readLines('UTF-8').findAll { !it.startsWith('#@') }.join('\\n'))
System.exit(0)
''',encoding='utf-8')
    home=Path(args.fiji_home)
    proc=_execute([str(java),'-Xmx512m','-Djava.awt.headless=true','-cp',str(home/'jars/*')+';'+str(home/'plugins/*'),'groovy.ui.GroovyMain',str(runner)])
    (out/'groovy.log').write_text(proc.stdout+'\n'+proc.stderr,encoding='utf-8')
    if proc.returncode: raise RuntimeError('Groovy replay failed: '+proc.stderr)
    np.testing.assert_array_equal(read_labels(out/'fiji_shared/fiji_interactive_labels.tif'),read_labels(out/'fiji_shared/morpholibj_labels.tif'))
    print('PASS Groovy replay: same labels as Java bridge',flush=True)
    write_json(out/'summary.json',{'status':'passed','source':str(source),'cases':summary,'groovy_replay_exact':True})
    print('ALL CHECKS PASSED\nResults: '+str(out),flush=True)


if __name__=='__main__': main()
