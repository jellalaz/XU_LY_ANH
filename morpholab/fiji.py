"""Gọi Java thật của Fiji/MorphoLibJ để kiểm chứng, lưu ảnh và metric độc lập."""
from pathlib import Path
import subprocess
import os
import time
import tifffile
import numpy as np
from .io import write_json, read_labels, environment
from .metrics import compare_labels, evaluate
from .tasks import check_cancelled

ROOT=Path(__file__).resolve().parents[1]


def _execute(command, timeout=180):
    """Chạy tiến trình con có thời hạn; thu hồi tiến trình khi lỗi, hủy hoặc đóng app."""
    import subprocess
    started=time.monotonic()
    check_cancelled()
    flags={'stdout':subprocess.PIPE,'stderr':subprocess.PIPE,'text':True,
           'encoding':'utf-8','errors':'replace'}
    if os.name=='nt': flags['creationflags']=subprocess.CREATE_NO_WINDOW
    proc=subprocess.Popen(command,**flags)
    try:
        while True:
            check_cancelled()
            if time.monotonic()-started > timeout: raise TimeoutError('Fiji vượt thời gian chờ')
            try:
                stdout,stderr=proc.communicate(timeout=.2)
                return subprocess.CompletedProcess(command,proc.returncode,stdout,stderr)
            except subprocess.TimeoutExpired: pass
    finally:
        if proc.poll() is None: proc.kill()
        proc.communicate()


def installation(home=r'C:\Tools\Fiji'):
    """Tìm Java JDK, ImageJ và MorphoLibJ trong thư mục Fiji đã cài."""
    home=Path(home)
    java=next(iter(home.glob('java/**/bin/java.exe')),None)
    javac=next(iter(home.glob('java/**/bin/javac.exe')),None)
    ij=next(iter((home/'jars').glob('ij-*.jar')),None)
    morpho=next(iter((home/'plugins').glob('MorphoLibJ*.jar')),None)
    if not all((java,javac,ij,morpho)):
        raise FileNotFoundError('Không tìm thấy Java JDK/ImageJ/MorphoLibJ trong '+str(home))
    return java,javac,ij,morpho


def run_reference(result, folder, truth=None, home=r'C:\Tools\Fiji', native=False):
    """Xuất đầu vào TIFF và gọi JAR Fiji thật. Shared dùng chung ba ảnh; native tự xử lý từ ảnh xám chuẩn hóa. Java tính thêm metric độc lập."""
    folder=Path(folder).resolve(); folder.mkdir(parents=True,exist_ok=True)
    java,javac,ij,morpho=installation(home)
    build=ROOT/'build'; build.mkdir(exist_ok=True)
    source=ROOT/'fiji'/'MorphoBridge.java'
    cp=str(ij)+';'+str(morpho)
    compiled=build/'MorphoBridge.class'
    native_source=ROOT/'fiji'/'NativePipeline.java'
    if not compiled.exists() or not (build/'NativePipeline.class').exists() or compiled.stat().st_mtime < max(source.stat().st_mtime,native_source.stat().st_mtime):
        proc=_execute([str(javac),'-J-Xmx256m','-encoding','UTF-8','-cp',cp,'-d',str(build),str(source),str(native_source)])
        if proc.returncode: raise RuntimeError(proc.stdout+'\n'+proc.stderr)
    for key in ('elevation','markers','mask'):
        a=result.stages[key]
        # ImageJ đọc float32 nhất quán, kể cả ảnh ID marker.
        if key=='mask': a=a.astype(np.uint8)*255
        else: a=a.astype(np.float32)
        tifffile.imwrite(folder/(key+'.tif'),a)
    tifffile.imwrite(folder/'gray.tif',result.stages['gray'].astype(np.float32))
    gtfile=folder/'ground_truth.tif'
    if truth is not None:
        tifffile.imwrite(gtfile,np.asarray(truth,np.float32))
    elif gtfile.exists():
        gtfile.unlink()  # remove only stale GT in this explicit run folder
    start=time.perf_counter()
    if native:
        p=result.params
        command=['NativePipeline',str(folder),str(p.radius),str(p.h),str(p.connectivity),str(p.sigma),str(p.min_area),str(p.bright_foreground).lower()]
    else:
        command=['MorphoBridge',str(folder),str(result.params.connectivity)]
    proc=_execute([str(java),'-Xmx512m','-Djava.awt.headless=true','-cp',str(build)+';'+cp,*command])
    (folder/'bridge.log').write_text(proc.stdout+'\n'+proc.stderr,encoding='utf-8')
    if proc.returncode: raise RuntimeError('Fiji bridge thất bại: '+proc.stdout+'\n'+proc.stderr)
    labels=read_labels(folder/'morpholibj_labels.tif',result.labels.shape)
    comparison,diff=compare_labels(labels,result.labels)
    stats={'reference':'Actual Fiji ImageJ + MorphoLibJ Java API','jar':str(morpho),
        'protocol':('Independent native baseline; see native_parameters.txt for exact differences; square SE, Otsu 8-bit, opening reconstruction, ImageJ EDM, extended maxima.' if native else 'Same float32 elevation, markers, binary mask, connectivity; no watershed dams.'),
        'process_seconds_including_jvm':time.perf_counter()-start,'comparison':comparison,
        'environment':environment()}
    if truth is not None: stats['fiji_against_ground_truth']=evaluate(truth,labels)
    write_json(folder/'comparison.json',stats)
    tifffile.imwrite(folder/'disagreement.tif',diff.astype(np.uint8)*255)
    # Ghi chuỗi thư mục trực tiếp vào script, không nội suy thành lệnh shell.
    import json
    if native:
        # Các ảnh trung gian native do chính Fiji tự tính.
        for src,dst in [('native_elevation','elevation'),('native_markers','markers'),('native_mask','mask')]:
            import shutil
            shutil.copyfile(folder/(src+'.tif'),folder/(dst+'.tif'))
    script='''// Fiji Script Editor: language Groovy, then Run.
import ij.IJ
import inra.ijpb.watershed.Watershed
def dir = '''+json.dumps(folder.as_posix())+'''
def elevation = IJ.openImage(dir + "/elevation.tif")
def markers = IJ.openImage(dir + "/markers.tif")
def mask = IJ.openImage(dir + "/mask.tif")
def result = Watershed.computeWatershed(elevation, markers, mask, '''+str(result.params.connectivity)+''', false, false)
result.show()
IJ.saveAsTiff(result, dir + "/fiji_interactive_labels.tif")
'''
    (folder/'Run_in_Fiji.groovy').write_text(script,encoding='utf-8')
    return labels,stats,diff
