from dataclasses import dataclass, asdict
from time import perf_counter
import numpy as np
from scipy import ndimage as ndi
from skimage import filters, morphology, segmentation
from . import algorithms as own
from .io import normalized


@dataclass
class Parameters:
    engine: str = 'custom'
    mode: str = 'hmax'
    sigma: float = 1.0
    threshold: float = -1.0
    bright_foreground: bool = True
    operation: str = 'opening_reconstruction'
    shape: str = 'disk'
    radius: int = 1
    min_area: int = 25
    fill_holes: bool = True
    connectivity: int = 4
    h: float = 2.0
    adaptive_fraction: float = .15

    def validate(self):
        if self.engine not in ('custom','library') or self.mode not in ('ccl','raw','hmax','adaptive'):
            raise ValueError('Engine/mode không hợp lệ')
        if self.operation not in ('none','erosion','dilation','opening','closing','opening_closing','opening_reconstruction'):
            raise ValueError('Phép hình thái không hợp lệ')
        if not 0 <= self.sigma <= 20 or not (self.threshold == -1 or 0 <= self.threshold <= 1):
            raise ValueError('Sigma trong [0,20]; threshold = -1 (Otsu) hoặc [0,1]')
        if not np.isfinite([self.sigma,self.threshold,self.h,self.adaptive_fraction]).all():
            raise ValueError('Tham số phải hữu hạn')
        if not 0 < self.h <= 1000 or not 0 <= self.adaptive_fraction <= 1:
            raise ValueError('h > 0; adaptive fraction trong [0,1]')
        if int(self.min_area) != self.min_area or self.min_area < 0:
            raise ValueError('Diện tích tối thiểu phải là số nguyên không âm')
        own.offsets(self.connectivity)
        own.footprint(self.radius,self.shape)
        return self


@dataclass
class Result:
    params: Parameters
    stages: dict
    threshold: float
    timings: dict

    @property
    def labels(self):
        return self.stages['labels']


def run(image, params=None):
    p = Parameters(**asdict(params or Parameters())).validate()
    if np.asarray(image).ndim != 2 or not np.isfinite(image).all():
        raise ValueError('Pipeline yêu cầu ảnh 2D hữu hạn')
    start = last = perf_counter()
    timings = {}
    def mark(name):
        nonlocal last
        now = perf_counter(); timings[name] = now-last; last = now
    fp = own.footprint(p.radius,p.shape)
    neighbors = ndi.generate_binary_structure(2,1 if p.connectivity==4 else 2)
    def morph(a,op):
        if p.engine=='custom':
            return own.binary_morphology(a,fp,op)
        func = getattr(ndi,'binary_'+op)
        return func(a,structure=fp,border_value=0)
    def ccl(a):
        return own.connected_components(a,p.connectivity) if p.engine=='custom' else ndi.label(a,neighbors)[0].astype(np.int32)
    def recon(seed,mask):
        if p.engine=='custom':
            return own.reconstruction_dilation(seed,mask,p.connectivity)
        return morphology.reconstruction(seed,mask,method='dilation',footprint=neighbors)
    gray = normalized(image)
    smooth = ndi.gaussian_filter(gray,p.sigma) if p.sigma else gray.copy()
    threshold = float(filters.threshold_otsu(smooth)) if p.threshold==-1 and np.ptp(smooth)>0 else (0. if p.threshold==-1 else p.threshold)
    binary = smooth > threshold if p.bright_foreground else smooth < threshold
    stages = {'gray':gray,'smoothed':smooth,'binary':binary}
    mark('preprocess')
    stages['erosion'] = morph(binary,'erosion')
    stages['dilation'] = morph(binary,'dilation')
    mask = binary.copy()
    if p.operation == 'opening_reconstruction':
        mask = recon(stages['erosion'].astype(float),binary.astype(float))>0
    elif p.operation == 'opening_closing':
        mask = morph(morph(mask,'opening'),'closing')
    elif p.operation != 'none':
        mask = morph(mask,p.operation)
    stages['morphology'] = mask.copy()
    if p.fill_holes:
        # Reconstruction of exterior background with explicitly selected connectivity.
        bg = ~mask
        border = np.zeros_like(mask); border[[0,-1],:] = bg[[0,-1],:]; border[:,[0,-1]] = bg[:,[0,-1]]
        # Same explicitly documented connectivity is used in both engines here.
        mask = ~(recon(border.astype(float),bg.astype(float))>0)
    components = ccl(mask)
    areas = np.bincount(components.ravel())
    keep = areas >= p.min_area; keep[0] = False
    mask = keep[components]
    components = ccl(mask)
    stages.update(mask=mask,components=components)
    mark('morphology_and_ccl')
    if p.engine=='custom':
        distance = own.distance_transform(mask)
    else:
        distance = ndi.distance_transform_edt(np.pad(mask,1,constant_values=False))[1:-1,1:-1]
    # Export float32 so both Fiji and Python flood the same elevation precision.
    distance = distance.astype(np.float32)
    stages['distance'] = distance
    stages['elevation'] = -distance
    mark('distance')
    def maxima(a,h):
        if h > float(a.max(initial=0)):
            return np.zeros_like(a,bool)
        result = own.h_maxima(a,h,p.connectivity) if p.engine=='custom' else morphology.h_maxima(a,h,footprint=neighbors)
        return np.asarray(result,dtype=bool)
    if p.mode=='raw':
        peaks = morphology.local_maxima(distance,footprint=neighbors)&mask
    elif p.mode=='adaptive':
        peaks = np.zeros_like(mask)
        for label,box in enumerate(ndi.find_objects(components),1):
            if box is None: continue
            region = components[box]==label
            local = np.where(region,distance[box],0)
            height = max(p.h,p.adaptive_fraction*float(local.max()))
            peaks[box] |= maxima(local,height)&region
    else:
        peaks = maxima(distance,p.h)&mask
    markers = ccl(peaks)
    # Guarantee at least one seed for each nonempty component, documented fallback.
    seeded = set(np.unique(components[markers>0]))
    next_label = int(markers.max(initial=0))
    for label,box in enumerate(ndi.find_objects(components),1):
        if box is None or label in seeded: continue
        local = np.where(components[box]==label,distance[box],-1)
        pos = np.unravel_index(np.argmax(local),local.shape)
        next_label += 1
        markers[box][pos] = next_label
    stages['markers'] = markers
    mark('markers')
    if p.mode=='ccl':
        labels = components.copy()
    elif p.engine=='custom':
        labels = own.watershed(stages['elevation'],markers,mask,p.connectivity)
    else:
        labels = segmentation.watershed(stages['elevation'],markers,connectivity=neighbors,mask=mask,watershed_line=False).astype(np.int32)
    labels = segmentation.relabel_sequential(labels)[0].astype(np.int32)
    stages['labels'] = labels
    mark('watershed')
    timings['total'] = perf_counter()-start
    return Result(p,stages,threshold,timings)
