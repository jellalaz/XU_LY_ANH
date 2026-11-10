def _squared_edt_1d(f):
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
