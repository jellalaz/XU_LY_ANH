"""Educational implementations. No skimage segmentation calls in this module.

All images are 2D. Binary morphology uses zero padding and a centered odd SE.
Distance uses a one-pixel background frame. Connectivity is explicitly 4 or 8.
"""
from collections import deque
import heapq
import numpy as np
from .tasks import check_cancelled


def offsets(connectivity=4):
    if connectivity not in (4, 8):
        raise ValueError("Connectivity must be 4 or 8")
    return [(y, x) for y in (-1, 0, 1) for x in (-1, 0, 1)
            if (y or x) and (connectivity == 8 or abs(y) + abs(x) == 1)]


def footprint(radius=1, shape="disk"):
    if int(radius) != radius or not 0 <= radius <= 50:
        raise ValueError("SE radius must be an integer in [0, 50]")
    y, x = np.mgrid[-radius:radius+1, -radius:radius+1]
    if shape == "disk":
        return x*x + y*y <= radius*radius
    if shape == "square":
        return np.ones(y.shape, bool)
    if shape == "cross":
        return (x == 0) | (y == 0)
    raise ValueError("Unknown SE shape")


def binary_morphology(image, se, operation):
    a = np.asarray(image, bool)
    se = np.asarray(se, bool)
    if a.ndim != 2 or se.ndim != 2 or any(s % 2 == 0 for s in se.shape) or not se.any():
        raise ValueError("Require 2D image and non-empty odd-sized SE")
    if operation == "opening":
        return binary_morphology(binary_morphology(a, se, "erosion"), se, "dilation")
    if operation == "closing":
        return binary_morphology(binary_morphology(a, se, "dilation"), se, "erosion")
    if operation not in ("erosion", "dilation"):
        raise ValueError("Unknown morphological operation")
    ry, rx = np.array(se.shape) // 2
    padded = np.pad(a, ((ry, ry), (rx, rx)), constant_values=False)
    result = np.full(a.shape, operation == "erosion", bool)
    for y, x in np.argwhere(se):
        check_cancelled()
        dy, dx = int(y - ry), int(x - rx)
        # Dilation samples x-b; erosion samples x+b (important for asymmetric SE).
        sign = -1 if operation == "dilation" else 1
        starty, startx = ry + sign*dy, rx + sign*dx
        shifted = padded[starty:starty+a.shape[0], startx:startx+a.shape[1]]
        if operation == "dilation":
            result |= shifted
        else:
            result &= shifted
    return result


def connected_components(mask, connectivity=4):
    a = np.asarray(mask, bool)
    if a.ndim != 2:
        raise ValueError("Expected 2D mask")
    neighbors = offsets(connectivity)
    out = np.zeros(a.shape, np.int32)
    h, w = a.shape
    label = 0
    visited=0
    for y, x in zip(*np.nonzero(a)):
        if x == 0 or (int(y)*w+int(x))%2048 == 0: check_cancelled()
        if out[y, x]:
            continue
        label += 1
        out[y, x] = label
        q = deque([(int(y), int(x))])
        while q:
            visited+=1
            if visited%2048 == 0: check_cancelled()
            cy, cx = q.popleft()
            for dy, dx in neighbors:
                ny, nx = cy+dy, cx+dx
                if 0 <= ny < h and 0 <= nx < w and a[ny,nx] and out[ny,nx] == 0:
                    out[ny,nx] = label
                    q.append((ny,nx))
    return out


def reconstruction_dilation(seed, mask, connectivity=4):
    """Geodesic dilation to fixed point using a propagation queue (gray/binary)."""
    seed, mask = np.asarray(seed, float), np.asarray(mask, float)
    if seed.shape != mask.shape or seed.ndim != 2 or not np.isfinite(seed).all() or not np.isfinite(mask).all():
        raise ValueError("Seed and mask must be finite 2D arrays of equal shape")
    if np.any(seed > mask):
        raise ValueError("Dilation reconstruction requires seed <= mask")
    # One synchronous dilation initializes only changed sites. Unchanged sites
    # have already propagated their original values to every neighbor in this
    # pass. Further increases therefore need propagation only from changed sites.
    neighbors = offsets(connectivity)
    h,w=seed.shape
    padded=np.pad(seed,1,constant_values=-np.inf)
    result=seed.copy()
    for dy,dx in neighbors:
        np.maximum(result,padded[1+dy:1+dy+h,1+dx:1+dx+w],out=result)
    np.minimum(result,mask,out=result)
    h, w = result.shape
    pending = result > seed
    q = deque(zip(*np.nonzero(pending)))
    steps=0
    while q:
        steps+=1
        if steps%2048==0: check_cancelled()
        y, x = q.popleft()
        pending[y,x] = False
        value = result[y,x]
        for dy, dx in neighbors:
            ny, nx = y+dy, x+dx
            if 0 <= ny < h and 0 <= nx < w:
                candidate = min(value, mask[ny,nx])
                if candidate > result[ny,nx]:
                    result[ny,nx] = candidate
                    if not pending[ny,nx]:
                        pending[ny,nx] = True
                        q.append((ny,nx))
    return result


def _squared_edt_1d(f):
    """Lower parabola envelope, O(n); Felzenszwalb & Huttenlocher (2012).

    Independently written Python implementation of the published algorithm;
    computes min_i ((x-i)^2 + f[i]), skipping infinite-cost sites.
    """
    n = len(f)
    sites = np.flatnonzero(np.isfinite(f))
    if not sites.size:
        return np.full(n, np.inf)
    v = np.empty(n, int)
    z = np.empty(n+1, float)
    k = 0
    v[0] = sites[0]
    z[0], z[1] = -np.inf, np.inf
    for q in sites[1:]:
        s = ((f[q] + q*q) - (f[v[k]] + v[k]*v[k])) / (2.0*(q-v[k]))
        while s <= z[k]:
            k -= 1
            s = ((f[q]+q*q)-(f[v[k]]+v[k]*v[k]))/(2.0*(q-v[k]))
        k += 1
        v[k], z[k], z[k+1] = q, s, np.inf
    result = np.empty(n, float)
    k = 0
    for q in range(n):
        while z[k+1] < q:
            k += 1
        result[q] = (q-v[k])**2 + f[v[k]]
    return result


def distance_transform(mask):
    """Exact Euclidean distance to background; separable squared EDT."""
    a = np.pad(np.asarray(mask, bool), 1, constant_values=False)
    f = np.where(a, np.inf, 0.0)
    for x in range(f.shape[1]):
        if x%32==0: check_cancelled()
        f[:,x] = _squared_edt_1d(f[:,x])
    for y in range(f.shape[0]):
        if y%32==0: check_cancelled()
        f[y,:] = _squared_edt_1d(f[y,:])
    return np.sqrt(f[1:-1,1:-1])


def h_maxima(image, height, connectivity=4):
    if height <= 0:
        raise ValueError("h must be > 0")
    a = np.asarray(image, float)
    reconstructed = reconstruction_dilation(a-height, a, connectivity)
    return (a-reconstructed) >= height-1e-9


def watershed(elevation, markers, mask, connectivity=4):
    """Seeded priority flood without dams.

    Heap key = (maximum elevation along path, FIFO arrival). Marked pixels are
    immutable. Equal-cost plateaus are assigned by arrival order. This tie rule
    is documented; exact boundaries need not match another implementation.
    """
    a = np.asarray(elevation, float)
    marker = np.asarray(markers)
    valid = np.asarray(mask, bool)
    if a.shape != marker.shape or a.shape != valid.shape or a.ndim != 2:
        raise ValueError("Elevation, markers and mask must have equal 2D shapes")
    if not np.isfinite(a).all() or np.any(marker < 0) or np.any(marker != np.floor(marker)):
        raise ValueError("Finite elevation and nonnegative integer markers required")
    if np.any((marker > 0) & ~valid):
        raise ValueError("Markers must be inside the mask")
    out = marker.astype(np.int32).copy()
    queued = out > 0
    heap = []
    age = 0
    for y, x in zip(*np.nonzero(out)):
        heapq.heappush(heap, (float(a[y,x]), age, int(y), int(x)))
        age += 1
    neighbors = offsets(connectivity)
    h, w = a.shape
    steps=0
    while heap:
        steps+=1
        if steps%2048==0: check_cancelled()
        cost, _, y, x = heapq.heappop(heap)
        for dy, dx in neighbors:
            ny, nx = y+dy, x+dx
            if 0 <= ny < h and 0 <= nx < w and valid[ny,nx] and not queued[ny,nx]:
                queued[ny,nx] = True
                out[ny,nx] = out[y,x]
                heapq.heappush(heap, (max(cost,float(a[ny,nx])), age, ny, nx))
                age += 1
    return out
