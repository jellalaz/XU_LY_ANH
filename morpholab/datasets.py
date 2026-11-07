"""Download official BBBC039 or generate reproducible, explicitly synthetic data."""
from pathlib import Path
from urllib.request import urlopen
import hashlib
import json
import zipfile
import shutil
import numpy as np
import tifffile
from scipy import ndimage as ndi
from skimage.measure import label
from PIL import Image
from .io import write_json

SOURCE = 'https://bbbc.broadinstitute.org/BBBC039'
BASE = 'https://data.broadinstitute.org/bbbc/BBBC039/'


def prepare_bbbc(root='data', progress=print):
    root=Path(root); raw=root/'raw'; target=root/'bbbc039'
    raw.mkdir(parents=True,exist_ok=True)
    for part in ('images','masks','metadata'):
        archive=raw/f'bbbc039_{part}.zip'
        if not archive.exists() or not zipfile.is_zipfile(archive):
            progress(f'Tải BBBC039 {part}...')
            temp=archive.with_suffix('.part')
            with urlopen(BASE+part+'.zip',timeout=120) as response, temp.open('wb') as dest:
                shutil.copyfileobj(response,dest)
            if not zipfile.is_zipfile(temp):
                raise ValueError('Tệp tải về không phải ZIP hợp lệ')
            temp.replace(archive)
        with zipfile.ZipFile(archive) as z:
            for name in z.namelist():
                # Extract only expected direct children; never arbitrary paths.
                p=Path(name)
                if len(p.parts)!=2 or p.parts[0]!=part or p.name.startswith('.') or name.endswith('/'):
                    continue
                dest=target/part/p.name; dest.parent.mkdir(parents=True,exist_ok=True)
                if not dest.exists():
                    with z.open(name) as src, dest.open('wb') as out: shutil.copyfileobj(src,out)
    split_of={}
    for split in ('training','validation','test'):
        for name in (target/'metadata'/f'{split}.txt').read_text().splitlines():
            split_of[Path(name.strip()).stem]=split
    records=[]
    for image in sorted((target/'images').glob('*.tif')):
        mask=target/'masks'/(image.stem+'.png')
        if not mask.exists(): continue
        out=target/'labels'/(image.stem+'.tif'); out.parent.mkdir(exist_ok=True)
        if not out.exists():
            rgb=np.asarray(Image.open(mask))
            # Official author decoder: connected equal-valued regions of channel 0.
            channel=rgb[...,0] if rgb.ndim==3 else rgb
            labels=label(channel,background=0,connectivity=2).astype(np.uint32)
            tifffile.imwrite(out,labels)
        records.append({'id':image.stem,'image':str(image.relative_to(root)),
            'truth':str(out.relative_to(root)),'split':split_of.get(image.stem,'unassigned'),
            'source':'BBBC039v1'})
    manifest={'source':SOURCE,'license':'CC0','root':str(root.resolve()),'records':records,
        'decoder':'Connected equal-valued regions in PNG channel 0; 8-connectivity; background 0.',
        'decoder_source':'https://gist.github.com/jccaicedo/15e811722fca51e3ae90e8b43057f075',
        'archives_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in raw.glob('bbbc039_*.zip')}}
    write_json(target/'manifest.json',manifest)
    progress(f'BBBC039 sẵn sàng: {len(records)} ảnh; giữ nguyên phân chia chính thức.')
    return target/'manifest.json'


def synthetic(root='data', count=18, seed=20261108):
    root=Path(root); target=root/'synthetic'; target.mkdir(parents=True,exist_ok=True)
    records=[]
    for i in range(count):
        rng=np.random.default_rng(seed+i)
        size=192
        yy,xx=np.mgrid[:size,:size]
        n=7+i%4
        centers=[]
        for k in range(n):
            for attempt in range(100):
                cy,cx=rng.uniform(24,size-24,2)
                radius=float(rng.uniform(10,23))
                if all(np.hypot(cy-y,cx-x)>max(10,.65*(radius+r)) for y,x,r in centers): break
            centers.append((cy,cx,radius))
        distances=np.stack([((yy-y)**2+(xx-x)**2)/r**2 for y,x,r in centers])
        nearest=distances.argmin(0)
        valid=distances.min(0)<=1
        truth=np.where(valid,nearest+1,0).astype(np.uint16)
        intensity=rng.uniform(.55,.95,n)
        image=np.full((size,size),.09)
        image[valid]=intensity[nearest[valid]]
        image=ndi.gaussian_filter(image,.7)
        noise=[.015,.04,.08][i%3]
        image=np.clip(image+.04*xx/size+rng.normal(0,noise,image.shape),0,1)
        name=f'synth_{i:02d}'
        imagepath=target/(name+'.tif'); truthpath=target/(name+'_gt.tif')
        tifffile.imwrite(imagepath,(image*65535).astype(np.uint16))
        tifffile.imwrite(truthpath,truth)
        records.append({'id':name,'image':str(imagepath.relative_to(root)),
            'truth':str(truthpath.relative_to(root)),'split':'validation' if i<6 else 'test',
            'source':'synthetic','seed':seed+i,'noise_sigma':noise,'true_objects':int(np.unique(truth[truth>0]).size)})
    write_json(target/'manifest.json',{'source':'Locally generated disks with normalized-nearest-center overlap ownership; not biological ground truth.',
        'root':str(root.resolve()),'seed':seed,'records':records})
    return target/'manifest.json'


def records(manifest, split=None, limit=None):
    data=json.loads(Path(manifest).read_text(encoding='utf-8'))
    root=Path(data['root'])
    # Locate data relative to manifest, so moving the project remains supported.
    if not root.exists(): root=Path(manifest).resolve().parent.parent
    rows=[r for r in data['records'] if split is None or r['split']==split]
    if limit: rows=rows[:limit]
    return [(r,root/r['image'],root/r['truth']) for r in rows]
