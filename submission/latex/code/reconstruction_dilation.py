def reconstruction_dilation(seed, mask, connectivity=4):
    seed, mask = np.asarray(seed, float), np.asarray(mask, float)
    if seed.shape != mask.shape or seed.ndim != 2 or not np.isfinite(seed).all() or not np.isfinite(mask).all():
        raise ValueError("Seed and mask must be finite 2D arrays of equal shape")
    if np.any(seed > mask):
        raise ValueError("Dilation reconstruction requires seed <= mask")
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
