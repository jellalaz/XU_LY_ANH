def watershed(elevation, markers, mask, connectivity=4):
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
