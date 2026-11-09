"""Scientific report figures from real saved experiment arrays."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import os
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'outputs/.matplotlib'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import tifffile,json
from skimage.color import label2rgb
from morpholab.io import overlay,read_image,read_labels
from morpholab.datasets import records
OUT=ROOT/'submission/latex/figures';OUT.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'figure.facecolor':'white'})

def panel(name,arrays,titles,columns=3,labels=()):
    rows=(len(arrays)+columns-1)//columns
    fig,axes=plt.subplots(rows,columns,figsize=(12,rows*3.5),squeeze=False)
    for i,(a,title) in enumerate(zip(arrays,titles)):
        ax=axes.flat[i]
        if i in labels:a=label2rgb(a,bg_label=0)
        ax.imshow(a,cmap='magma' if 'cách' in title else 'gray',interpolation='nearest')
        ax.set_title(title,pad=9);ax.axis('off')
    for ax in axes.flat[len(arrays):]:ax.axis('off')
    fig.tight_layout();fig.savefig(OUT/name,dpi=190,bbox_inches='tight');plt.close(fig)

folder=ROOT/'outputs/demo_shared'
keys=['gray','binary','mask','distance','markers','labels']
panel('pipeline.png',[tifffile.imread(folder/(k+'.tif')) for k in keys],['(a) Ảnh gốc','(b) Phân ngưỡng','(c) Mask sau hình thái','(d) Khoảng cách tới nền','(e) Marker (hạt giống)','(f) Nhãn Watershed'],labels=(4,5))
native=ROOT/'outputs/academic_smoke_20261108_200116/fiji_native'
print([p.name for p in native.glob('native*.tif')])
# Morphology example uses independent native Fiji intermediates saved by Java.
keys=['native_binary','native_erosion','native_dilation','native_opening','native_closing','native_reconstruction']
files=[native/(k+'.tif') for k in keys]
if all(p.exists() for p in files):
    panel('morphology.png',[tifffile.imread(p) for p in files],['(a) Nhị phân ban đầu','(b) Erosion (co)','(c) Dilation (giãn)','(d) Opening (mở)','(e) Closing (đóng)','(f) Reconstruction (tái tạo)'])
smoke=ROOT/'outputs/academic_smoke_20261108_200116'
panel('ccl_watershed.png',[read_image(ROOT/'data/synthetic/synth_00.tif'),read_labels(smoke/'ccl/labels.tif'),read_labels(smoke/'hmax/labels.tif')],['(a) Đầu vào: 7 vật thể','(b) CCL: 5 vùng','(c) Watershed: 7 vùng'],labels=(1,2))
record,image,truth=records(ROOT/'data/bbbc039/manifest.json','test',1)[0]
id=record['id']
base=ROOT/'outputs/v2_compare_bbbc039_test/fiji_runs'/id
print('Real example',id,[p.name for p in base.glob('*')][:6])
gray=read_image(image);gt=read_labels(truth)
from morpholab.pipeline import Parameters,run
pred=run(gray,Parameters()).labels
fiji=read_labels(base/'fiji-native/morpholibj_labels.tif') if (base/'fiji-native/morpholibj_labels.tif').exists() else None
if fiji is None:
    from morpholab.fiji import run_reference
    fiji,_,_=run_reference(run(gray,Parameters()),ROOT/'outputs/latex_real_native',gt,native=True)
panel('real_example.png',[gray,label2rgb(gt,bg_label=0),overlay(gray,pred),overlay(gray,fiji)],['(a) Ảnh thật BBBC039','(b) Nhãn đúng từng nhân','(c) Python tự cài','(d) Fiji native'],columns=2)
print('Figures written:',OUT)
