"""Integration tests use actual local Fiji when installed; no mock reference."""
from pathlib import Path
import tempfile
import unittest
import csv
import numpy as np
from morpholab.pipeline import run,Parameters
from morpholab.metrics import evaluate
from morpholab.fiji import installation,run_reference


class FijiIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try: installation()
        except FileNotFoundError: raise unittest.SkipTest('Fiji/MorphoLibJ not installed on this machine')

    def sample(self):
        y,x=np.mgrid[:48,:64]
        a=(y-22)**2+(x-19)**2<12**2
        b=(y-24)**2+(x-38)**2<12**2
        gt=np.where(a,1,np.where(b,2,0)).astype(np.int32)
        return run((a|b).astype(float),Parameters(sigma=0,radius=0)),gt

    def test_shared_inputs_and_independent_java_metrics(self):
        result,gt=self.sample()
        with tempfile.TemporaryDirectory() as folder:
            labels,stats,_=run_reference(result,folder,gt)
            self.assertEqual(np.unique(labels[labels>0]).size,2)
            self.assertTrue(np.all(labels[~result.stages['mask']]==0))
            py=evaluate(gt,labels)
            with (Path(folder)/'fiji_metrics.csv').open() as f: java=next(csv.DictReader(f))
            self.assertAlmostEqual(float(java['foreground_iou']),py['foreground_iou'])
            self.assertAlmostEqual(float(java['foreground_dice']),py['foreground_dice'])
            self.assertEqual(int(java['predicted_objects']),py['predicted_objects'])
            self.assertGreater(stats['comparison']['matched_pixel_agreement_foreground_union'],.9)

    def test_native_fiji_workflow_exports_every_operator(self):
        result,gt=self.sample()
        with tempfile.TemporaryDirectory() as folder:
            labels,stats,_=run_reference(result,folder,gt,native=True)
            for stage in ('erosion','dilation','opening','closing','reconstruction','distance','components','markers'):
                self.assertTrue((Path(folder)/('native_'+stage+'.tif')).is_file())
            self.assertGreater(evaluate(gt,labels)['object_f1'],.9)


if __name__=='__main__': unittest.main()
