def x(p0, p1):
    d = abs(p0 - p1)
    if d > 2:
        return []
    elif d == 2:
        return [(p0 + p1) / 2]
    else:
        m = (p0 + p1) / 2
        v = m - p0
        w = complex(v.imag, -v.real)
        l = abs(w)
        h = (1 - l ** 2) ** .5 * w / l
        return [m + h, m - h]

for e in iter(input, '0'):
    n = int(e)
    P = [complex(*map(float, input().split(','))) for _ in [0] * n]
    Q = []
    for i in range(n):
        for j in range(i + 1, n):
            Q += x(P[i], P[j])
    print(max([sum(1.01 >= abs(q - p) for p in P) for q in Q] + [1]))
