from dataclasses import replace
from pathlib import Path
import ctypes
import json
import os
import sys
import tempfile
import threading
import time
import unittest
import numpy as np
import tifffile
from skimage.morphology import reconstruction
from morpholab.algorithms import reconstruction_dilation
from morpholab.pipeline import run,Parameters
from morpholab.tasks import Cancellation,Cancelled,task_scope
from morpholab.sessions import save_session,load_session,history
from morpholab.studies import study
from morpholab.fiji import _execute


class WorkspaceTest(unittest.TestCase):
    def sample(self):
        y,x=np.mgrid[:35,:43]
        gt=np.where((y-14)**2+(x-14)**2<9**2,1,np.where((y-21)**2+(x-30)**2<8**2,2,0)).astype(np.int32)
        return (gt>0).astype(float),gt

    def test_reconstruction_randomized_float_and_flat_cases(self):
        rng=np.random.default_rng(87)
        for conn in (4,8):
            fp=np.ones((3,3)) if conn==8 else np.array([[0,1,0],[1,1,1],[0,1,0]])
            for _ in range(12):
                mask=rng.normal(size=(14,17))
                seed=mask-rng.random(mask.shape)*3
                np.testing.assert_allclose(reconstruction_dilation(seed,mask,conn),reconstruction(seed,mask,footprint=fp))
        seed=np.ones((30,40))
        np.testing.assert_array_equal(reconstruction_dilation(seed,seed),seed)

    def test_manual_markers_and_validation(self):
        image,gt=self.sample(); p=Parameters(sigma=0,radius=0,h=2)
        result=run(image,p); markers=result.stages['markers'].copy()
        actual=run(image,p,manual_markers=markers)
        np.testing.assert_array_equal(result.labels,actual.labels)
        self.assertIn('manual_markers',actual.stages)
        markers[0,0]=8
        with self.assertRaises(ValueError): run(image,p,manual_markers=markers)
        with self.assertRaises(ValueError): run(image,p,manual_markers=np.zeros(image.shape,int))
        with self.assertRaises(ValueError): run(image,replace(p,mode='ccl'),manual_markers=gt)

    def test_portable_session_and_html_escaped(self):
        image,gt=self.sample(); result=run(image,Parameters(sigma=0))
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)/'one'
            save_session(result,image,folder,gt,result.labels,source='<script>bad()</script>')
            loaded=load_session(folder)
            np.testing.assert_array_equal(loaded.image,image)
            np.testing.assert_array_equal(loaded.result.labels,result.labels)
            np.testing.assert_array_equal(loaded.truth,gt)
            self.assertEqual(loaded.result.params,result.params)
            self.assertEqual(len(history(temp)),1)
            with self.assertRaises(FileExistsError): save_session(result,image,folder,gt)
            html=(folder/'report.html').read_text(encoding='utf-8')
            self.assertNotIn('<script>bad()',html)
            self.assertIn('&lt;script&gt;',html)
            meta=json.loads((folder/'run.json').read_text(encoding='utf-8'))
            meta['stages'].append('../outside')
            (folder/'run.json').write_text(json.dumps(meta),encoding='utf-8')
            with self.assertRaises(ValueError): load_session(folder)

    def manifest(self,temp):
        image,gt=self.sample(); root=Path(temp)
        tifffile.imwrite(root/'image.tif',image); tifffile.imwrite(root/'gt.tif',gt)
        manifest=root/'manifest.json'
        manifest.write_text(json.dumps({'root':str(root),'records':[
            {'id':f'sample_{i}','image':'image.tif','truth':'gt.tif','split':'validation'} for i in range(2)]}),encoding='utf-8')
        return manifest

    def test_study_ablation_and_deterministic_corruptions(self):
        with tempfile.TemporaryDirectory() as temp:
            manifest=self.manifest(temp)
            p=Parameters(engine='library',sigma=0)
            a,s=study(manifest,Path(temp)/'ablation',p,kind='ablation',limit=1,repeats=1,progress=lambda s:None)
            self.assertEqual(len(a),7); self.assertTrue((a.status=='ok').all())
            self.assertTrue((Path(temp)/'ablation/report.html').exists())
            a,_=study(manifest,Path(temp)/'r1',p,kind='robustness',limit=1,repeats=1,progress=lambda s:None)
            b,_=study(manifest,Path(temp)/'r2',p,kind='robustness',limit=1,repeats=1,progress=lambda s:None)
            np.testing.assert_array_equal(a.object_f1,b.object_f1)
            with self.assertRaises(FileExistsError): study(manifest,Path(temp)/'r1',p,progress=lambda s:None)

    def test_cancel_partial_study_is_marked_cancelled(self):
        with tempfile.TemporaryDirectory() as temp:
            manifest=self.manifest(temp); token=Cancellation(); calls=[]
            def progress(message):
                calls.append(message)
                if len(calls)==2: token.cancel()
            with self.assertRaises(Cancelled),task_scope(token):
                study(manifest,Path(temp)/'partial',Parameters(engine='library'),kind='ablation',limit=1,repeats=1,progress=progress)
            data=json.loads((Path(temp)/'partial/study.json').read_text(encoding='utf-8'))
            self.assertEqual(data['status'],'cancelled')
            self.assertTrue((Path(temp)/'partial/summary.csv').exists())

    def test_cancel_child_is_reaped(self):
        with tempfile.TemporaryDirectory() as temp:
            pidfile=Path(temp)/'pid.txt'; token=Cancellation()
            command=[sys.executable,'-c','import os,time,pathlib; pathlib.Path('+repr(str(pidfile))+').write_text(str(os.getpid())); time.sleep(20)']
            timer=threading.Timer(.6,token.cancel); timer.start(); started=time.monotonic()
            try:
                with self.assertRaises(Cancelled),task_scope(token): _execute(command)
            finally: timer.cancel()
            self.assertLess(time.monotonic()-started,5)
            if pidfile.exists() and os.name=='nt':
                pid=int(pidfile.read_text())
                handle=ctypes.windll.kernel32.OpenProcess(0x00100000,False,pid)
                if handle:
                    try: self.assertNotEqual(ctypes.windll.kernel32.WaitForSingleObject(handle,0),258)
                    finally: ctypes.windll.kernel32.CloseHandle(handle)


if __name__=='__main__': unittest.main()
