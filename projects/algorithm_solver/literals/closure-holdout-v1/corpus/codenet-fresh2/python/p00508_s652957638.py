# coding: utf-8

def closest_pair(P, n):
    if n <= 1:
        return float('inf')

    m = n // 2
    x = P[m][0]
    d = min(closest_pair(P[:m], m), closest_pair(P[m:], n-m))
    P.sort(key=lambda p: p[1])

    Q = []
    for p in P:
        if (p[0] - x)**2 >= d:
            continue

        for q in Q:
            dx = p[0] - q[0]
            dy = p[1] - q[1]

            if dy**2 >= d:
                break

            d = min(d, dx**2 + dy**2)

        Q.insert(0, p)

    return d


N = int(input())
P = [list(map(int, input().split())) for _ in range(N)]
P.sort()
print(closest_pair(P, N))



