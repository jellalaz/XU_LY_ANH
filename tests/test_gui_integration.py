"""Real Tk callback workflows; opt in on an unlocked desktop with the ai env.

MORPHOLAB_DESKTOP_TEST=1 python -B -m unittest discover -s tests -p test_gui_integration.py -v
The window stays withdrawn; the worker, core algorithms and Java bridge are real.
"""
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import json
import os
import tempfile
import time
import tkinter as tk
from tkinter import ttk
import unittest
import numpy as np
import tifffile
from morpholab.gui import App, ROOT
from morpholab.pipeline import Parameters
from morpholab.ui import ChoiceVar, CHOICES


@unittest.skipUnless(os.environ.get('MORPHOLAB_DESKTOP_TEST')=='1','Opt-in real Tk desktop test')
class DesktopWorkflowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='morpholab_ui_')
        cls.folder=Path(cls.temp.name)
        cls.root=tk.Tk(); cls.root.withdraw(); cls.app=App(cls.root)
        cls.errors=[]; cls.app.error=cls.errors.append
        cls.sequence=0
        def output(prefix):
            cls.sequence+=1
            return cls.folder/f'{prefix}_{cls.sequence}'
        cls.app.output_folder=output

    @classmethod
    def tearDownClass(cls):
        cls.app.close(); cls.temp.cleanup()

    def setUp(self):
        self.errors.clear(); self.app.reset_config(); self.app.demo()
        self.root.update()

    def finish(self,timeout=50):
        end=time.monotonic()+timeout
        while self.app.busy and time.monotonic()<end:
            self.root.update(); time.sleep(.01)
        self.root.update()
        self.assertFalse(self.app.busy,'Worker did not complete')
        self.assertEqual(self.errors,[])

    def segment(self):
        self.app.segment()
        self.assertTrue(all(str(w.cget('state'))=='disabled' for w,_ in self.app.input_widgets))
        self.finish()
        self.assertTrue(all(str(w.cget('state'))==state for w,state in self.app.input_widgets))
        self.assertEqual(float(self.app.progress['value']),0)

    def test_choices_roundtrip_through_actual_combobox(self):
        for group in ('engine','mode','operation','shape','connectivity','dataset','split','study','view'):
            var=ChoiceVar(self.root,group=group,value=next(iter(CHOICES[group])))
            box=ttk.Combobox(self.root,textvariable=var,values=var.display_values)
            for index,(key,label) in enumerate(CHOICES[group].items()):
                box.current(index)
                self.assertEqual(var.get(),key)
                self.assertEqual(box.get(),label)
                var.set(key); self.assertEqual(box.get(),label)
            box.destroy()
        p=self.folder/'config.json'
        with patch('morpholab.gui.filedialog.asksaveasfilename',return_value=str(p)):
            self.app.save_config()
        self.assertEqual(json.loads(p.read_text(encoding='utf-8')),asdict(Parameters()))
        self.app.vars['mode'].set('ccl')
        with patch('morpholab.gui.filedialog.askopenfilename',return_value=str(p)):
            self.app.load_config()
        self.assertEqual(self.app.parameters(),Parameters())

    def test_empty_result_stale_parameters_and_no_truth(self):
        self.segment()
        self.assertEqual(self.app.cards['objects'].get(),'7')
        self.assertEqual(self.app.cards['f1'].get(),'1.000')
        self.app.vars['min_area'].set('100000')
        self.assertIn('Đã đổi tham số',self.app.notice.get())
        self.app.fiji()
        self.assertIn('lần chạy trước',self.errors.pop())
        self.segment()
        self.assertEqual(self.app.cards['objects'].get(),'0')
        self.assertEqual(self.app.cards['f1'].get(),'0.000')
        self.assertIn('lớn hơn toàn ảnh',self.app.notice.get())
        self.assertTrue(any('Không có đối tượng' in t.get_text() for a in self.app.fig.axes for t in a.texts))
        self.app.vars['radius'].set('')
        self.assertIn('chưa hợp lệ',self.app.notice.get())
        self.app.reset_config(); self.assertEqual(self.app.parameters(),Parameters())
        self.app.last_output=self.folder/'previous'
        self.app.set_image(ROOT/'data/synthetic/synth_00.tif')
        self.assertIsNone(self.app.last_output)
        self.segment(); self.assertEqual(self.app.cards['f1'].get(),'—')
        self.assertIn('Chưa có ground truth',self.app.notice.get())

    def test_manual_markers_apply_and_restore(self):
        self.segment(); expected=self.app.result.labels.copy()
        self.app.navigate('zoom'); self.assertTrue(self.app.toolbar.mode)
        self.app.marker_edit.set(True)
        self.assertFalse(self.app.toolbar.mode)
        candidates=np.argwhere(self.app.result.stages['mask'] & (self.app.manual_markers==0))
        y,x=candidates[len(candidates)//2]
        event=SimpleNamespace(inaxes=self.app.fig.axes[-1],xdata=float(x),ydata=float(y),button=1)
        self.app.inspect_object(event)
        self.assertTrue(self.app.marker_dirty)
        self.assertIn('chưa áp dụng',self.app.notice.get())
        self.app.export(); self.assertIn('chưa áp dụng',self.errors.pop())
        self.app.apply_markers(); self.finish()
        self.assertFalse(self.app.marker_dirty)
        self.assertIn('manual_markers',self.app.result.stages)
        self.app.reset_markers(); self.finish()
        np.testing.assert_array_equal(self.app.result.labels,expected)
        self.assertNotIn('manual_markers',self.app.result.stages)

    def test_fiji_export_restore_and_invalid_import(self):
        self.segment(); self.app.fiji(); self.finish()
        self.assertIsNotNone(self.app.reference)
        self.assertEqual(int(self.app.reference.max()),7)
        self.assertTrue((self.app.last_output/'fiji_metrics.csv').exists())
        expected=self.app.result.labels.copy(); reference=self.app.reference.copy()
        bad=self.folder/'bad_shape.tif'; tifffile.imwrite(bad,np.zeros((9,9),np.uint8))
        with patch('morpholab.gui.filedialog.askopenfilename',return_value=str(bad)):
            self.app.import_reference()
        self.assertEqual(len(self.errors),1); self.errors.clear()
        np.testing.assert_array_equal(self.app.reference,reference)
        with patch('morpholab.gui.filedialog.askdirectory',return_value=str(self.folder)):
            self.app.export()
        self.finish(); saved=self.app.last_output
        self.assertTrue((saved/'report.html').exists())
        self.app.set_image(ROOT/'data/synthetic/synth_01.tif')
        self.app.restore_session(saved); self.finish()
        np.testing.assert_array_equal(self.app.result.labels,expected)
        np.testing.assert_array_equal(self.app.reference,reference)
        self.assertEqual(self.app.parameters(),Parameters())
        self.assertEqual(self.app.cards['f1'].get(),'1.000')
        self.assertTrue(self.app.require_current_result())

    def test_benchmark_and_parameter_sweep(self):
        self.app.dataset.set('synthetic'); self.app.split.set('validation')
        self.app.limit.set('1'); self.app.repeats.set('1')
        self.app.benchmark(); self.finish()
        import pandas as pd
        summary=pd.read_csv(self.app.last_output/'summary.csv')
        self.assertEqual(len(summary),8)
        self.assertEqual(set(summary.engine),{'custom','library'})
        self.app.vars['mode'].set('ccl')
        self.app.sweep(); self.finish()
        self.assertTrue((self.app.last_output/'selected_parameters.json').exists())
        params=json.loads((self.app.last_output/'selected_parameters.json').read_text(encoding='utf-8'))
        self.assertEqual(params['engine'],'custom'); self.assertEqual(params['mode'],'hmax')
        experiment=json.loads((self.app.last_output/'h_0.5/experiment.json').read_text(encoding='utf-8'))
        self.assertEqual(experiment['engines'],['custom'])

    def test_batch_mixed_rgb_gray_ground_truth_and_bad_image(self):
        from PIL import Image
        source=self.folder/'mixed_input'; source.mkdir()
        image=np.zeros((40,60),np.uint8); image[5:25,5:25]=230; image[10:35,35:55]=150
        truth=np.zeros_like(image); truth[5:25,5:25]=1; truth[10:35,35:55]=2
        tifffile.imwrite(source/'gray.tif',image); tifffile.imwrite(source/'gray_gt.tif',truth)
        Image.fromarray(np.repeat(image[...,None],3,axis=2)).save(source/'color.png')
        tifffile.imwrite(source/'invalid.tif',np.zeros((5,9,11),np.uint8),photometric='minisblack')
        self.app.vars['engine'].set('library')
        with patch('morpholab.gui.filedialog.askdirectory',return_value=str(source)):
            self.app.batch_folder()
        self.finish()
        import pandas as pd
        table=pd.read_csv(self.app.last_output/'batch.csv').set_index('image')
        self.assertEqual(len(table),3)
        self.assertEqual(table.loc['color.png','status'],'ok')
        self.assertTrue(np.isnan(table.loc['color.png','object_f1']))
        self.assertEqual(table.loc['gray.tif','object_f1'],1)
        self.assertEqual(table.loc['invalid.tif','status'],'error')

    def test_research_four_backends_and_dataset_browser(self):
        self.app.dataset.set('synthetic'); self.app.split.set('validation')
        self.app.limit.set('1'); self.app.repeats.set('1'); self.app.study_kind.set('compare')
        self.app.run_study(); self.finish()
        self.assertEqual(len(self.app.study_table.get_children()),4)
        self.assertTrue((self.app.last_output/'report.html').exists())
        import pandas as pd
        frame=pd.read_csv(self.app.last_output/'per_image.csv')
        self.assertTrue((frame.status=='ok').all())
        self.app.browse_dataset(); self.root.update()
        windows=[w for w in self.root.winfo_children() if isinstance(w,tk.Toplevel)]
        self.assertEqual(len(windows),1)
        trees=[w for w in windows[0].winfo_children() if isinstance(w,ttk.Treeview)]
        self.assertGreater(len(trees[0].get_children()),0)
        windows[0].destroy()


if __name__=='__main__': unittest.main()
