import unittest
import numpy as np
from scipy import ndimage as ndi
from skimage import morphology,segmentation
from morpholab import algorithms as own
from morpholab.pipeline import run,Parameters
from morpholab.metrics import evaluate,compare_labels


class AlgorithmsTest(unittest.TestCase):
    def test_morphology_against_scipy_asymmetric_and_edges(self):
        rng=np.random.default_rng(52)
        for se in (own.footprint(2),own.footprint(1,'cross'),np.array([[0,1,0],[0,1,1],[0,0,0]],bool)):
            a=rng.random((17,21))>.4
            for op in ('erosion','dilation','opening','closing'):
                expected=getattr(ndi,'binary_'+op)(a,structure=se,border_value=0)
                np.testing.assert_array_equal(own.binary_morphology(a,se,op),expected)

    def test_reconstruction_gray_fixed_point_and_library(self):
        rng=np.random.default_rng(2)
        mask=rng.integers(0,15,(12,16)).astype(float)
        seed=np.minimum(mask,rng.integers(0,8,mask.shape))
        for conn in (4,8):
            fp=ndi.generate_binary_structure(2,1 if conn==4 else 2)
            actual=own.reconstruction_dilation(seed,mask,conn)
            expected=morphology.reconstruction(seed,mask,footprint=fp)
            np.testing.assert_array_equal(actual,expected)
            np.testing.assert_array_equal(own.reconstruction_dilation(actual,mask,conn),actual)
        with self.assertRaises(ValueError): own.reconstruction_dilation(mask+1,mask)

    def test_distance_transform_exact_with_background_frame(self):
        rng=np.random.default_rng(9)
        for mask in [np.ones((11,15),bool),np.zeros((11,15),bool),rng.random((17,22))>.15]:
            expected=ndi.distance_transform_edt(np.pad(mask,1))[1:-1,1:-1]
            np.testing.assert_allclose(own.distance_transform(mask),expected,atol=1e-12)

    def test_ccl_connectivity_and_id_independence(self):
        a=np.eye(7,dtype=bool)
        self.assertEqual(own.connected_components(a,4).max(),7)
        self.assertEqual(own.connected_components(a,8).max(),1)
        for conn in (4,8):
            rng=np.random.default_rng(45); mask=rng.random((25,28))>.6
            expected=ndi.label(mask,ndi.generate_binary_structure(2,1 if conn==4 else 2))[0]
            stats,_=compare_labels(expected,own.connected_components(mask,conn))
            self.assertEqual(stats['different_pixels'],0)

    def test_h_maxima_against_library(self):
        y,x=np.mgrid[:31,:37]
        a=np.maximum(8-np.hypot(y-11,x-12),5-np.hypot(y-17,x-24)).clip(0)
        for conn in (4,8):
            fp=ndi.generate_binary_structure(2,1 if conn==4 else 2)
            for h in (.5,2.,4.):
                np.testing.assert_array_equal(own.h_maxima(a,h,conn),morphology.h_maxima(a,h,footprint=fp))

    def test_watershed_disconnected_seed_invariants_and_library(self):
        y,x=np.mgrid[:30,:40]; elevation=np.minimum((y-14)**2+(x-10)**2,(y-14)**2+(x-29)**2).astype(float)
        mask=np.ones(elevation.shape,bool); markers=np.zeros(elevation.shape,np.int32)
        markers[14,10]=1; markers[14,29]=2
        for conn in (4,8):
            labels=own.watershed(elevation,markers,mask,conn)
            self.assertTrue(np.all(labels>0))
            np.testing.assert_array_equal(labels[markers>0],markers[markers>0])
            expected=segmentation.watershed(elevation,markers,mask=mask,connectivity=ndi.generate_binary_structure(2,1 if conn==4 else 2))
            self.assertGreater(evaluate(expected,labels)['object_f1'],.99)
        with self.assertRaises(ValueError): own.watershed(elevation,markers,np.zeros_like(mask))

    def test_empty_and_full_pipeline(self):
        for engine in ('custom','library'):
            empty=run(np.zeros((20,20)),Parameters(engine=engine))
            self.assertFalse(empty.labels.any())
            image=np.zeros((40,60)); image[8:30,10:50]=1
            result=run(image,Parameters(engine=engine,sigma=0))
            self.assertGreater(result.labels.max(),0)
            self.assertTrue(np.all(result.labels[~result.stages['mask']]==0))
            for comp in np.unique(result.stages['components']):
                if comp: self.assertTrue(np.any(result.stages['markers'][result.stages['components']==comp]>0))

    def test_pipeline_engines_intermediate_agreement(self):
        y,x=np.mgrid[:60,:70]; mask=((y-25)**2+(x-25)**2<17**2)|((y-30)**2+(x-45)**2<15**2)
        custom=run(mask.astype(float),Parameters(sigma=0,engine='custom'))
        library=run(mask.astype(float),Parameters(sigma=0,engine='library'))
        for key in ('mask','distance','markers'):
            np.testing.assert_allclose(custom.stages[key],library.stages[key])
        self.assertGreater(evaluate(custom.labels,library.labels)['object_f1'],.99)

    def test_adaptive_both_engines_multiple_components(self):
        image=np.zeros((40,60)); image[3:17,3:17]=1; image[20:36,30:53]=1
        for engine in ('custom','library'):
            result=run(image,Parameters(engine=engine,mode='adaptive',sigma=0,h=.5))
            self.assertGreaterEqual(result.labels.max(),2)
            self.assertFalse(result.labels[~result.stages['mask']].any())


class MetricsTest(unittest.TestCase):
    def test_permuted_ids_not_false_difference(self):
        gt=np.array([[0,1,1],[0,2,2]])
        pred=np.array([[0,88,88],[0,9,9]])
        self.assertEqual(evaluate(gt,pred)['object_f1'],1)
        self.assertEqual(compare_labels(gt,pred)[0]['different_pixels'],0)

    def test_merge_and_split_detected_despite_perfect_foreground(self):
        gt=np.array([[1,1,2,2],[1,1,2,2]])
        merged=np.ones_like(gt)
        stats=evaluate(gt,merged)
        self.assertEqual(stats['foreground_iou'],1)
        self.assertEqual(stats['merge_objects'],1)
        self.assertLess(stats['object_f1'],1)
        self.assertEqual(evaluate(merged,gt)['split_objects'],1)

    def test_empty_conventions_and_invalid_inputs(self):
        empty=np.zeros((5,5),int); full=np.ones_like(empty)
        self.assertEqual(evaluate(empty,empty)['object_f1'],1)
        self.assertEqual(evaluate(empty,full)['object_f1'],0)
        self.assertEqual(evaluate(full,empty)['object_f1'],0)
        with self.assertRaises(ValueError): evaluate(empty,np.zeros((2,2)))
        with self.assertRaises(ValueError): evaluate(empty,full*.5)
        with self.assertRaises(ValueError): evaluate(empty,full,iou_threshold=0)


if __name__=='__main__': unittest.main()
