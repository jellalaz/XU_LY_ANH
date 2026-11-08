"""Reproducible hand examples and controlled reconstruction timing, no GUI."""
from pathlib import Path
import sys, json, time, platform, argparse
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
from scipy.ndimage import grey_dilation,generate_binary_structure
from morpholab import algorithms as a
from morpholab.io import write_json,environment

ROOT=Path(__file__).resolve().parents[1]

def synchronous(seed,mask,conn):
    current=seed.copy(); iterations=0
    while True:
        updated=np.minimum(grey_dilation(current,footprint=generate_binary_structure(2,1 if conn==4 else 2),mode='constant',cval=-np.inf),mask)
        iterations+=1
        if np.array_equal(updated,current): return current,iterations
        current=updated

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',default=str(ROOT/'outputs/academic_checks'))
    OUT=Path(parser.parse_args().out).resolve()
    OUT.mkdir(parents=True,exist_ok=True)
    sample=np.zeros((7,7),bool); sample[2:5,2:5]=True
    se=a.footprint(1,'square')
    cases={'input':sample.astype(int).tolist(),'SE':se.astype(int).tolist()}
    for name in ('erosion','dilation','opening','closing'):
        cases[name]=a.binary_morphology(sample,se,name).astype(int).tolist()
    cases['distance']=a.distance_transform(sample).tolist()
    cases['diagonal_4']=a.connected_components(np.eye(3,dtype=bool),4).tolist()
    cases['diagonal_8']=a.connected_components(np.eye(3,dtype=bool),8).tolist()
    write_json(OUT/'hand_examples.json',cases)
    rows=[]
    for size in (48,96,160):
        mask=np.ones((size,size)); seed=np.zeros_like(mask); seed[size//2,size//2]=1
        expected,iterations=synchronous(seed,mask,4)
        np.testing.assert_array_equal(a.reconstruction_dilation(seed,mask,4),expected)
        for name,fn in [('synchronous_scipy',lambda:synchronous(seed,mask,4)[0]),('queue_python',lambda:a.reconstruction_dilation(seed,mask,4))]:
            fn()
            for repeat in range(5):
                start=time.perf_counter(); result=fn(); duration=time.perf_counter()-start
                np.testing.assert_array_equal(result,expected)
                rows.append(dict(size=size,pixels=size*size,method=name,repeat=repeat,seconds=duration,iterations=iterations,exact=True))
    frame=pd.DataFrame(rows); frame.to_csv(OUT/'timing.csv',index=False)
    summary=frame.groupby(['size','method']).seconds.agg(['median','min','max']).reset_index()
    summary.to_csv(OUT/'timing_summary.csv',index=False)
    write_json(OUT/'protocol.json',dict(environment=environment(),processor=platform.processor(),warmup=1,repeats=5,
        scope='Single bright seed reconstructs full constant mask, connectivity 4. Exact equality checked. Timing excludes IO and equality checks.',
        caveat='SciPy dilation is compiled while queue is Python. This tests practical implementations, not isolated asymptotic complexity or an old-versus-new speedup.'))
    print(summary.to_string(index=False))

if __name__=='__main__':main()
