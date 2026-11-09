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