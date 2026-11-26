def main():
    N, K = map(int,input().split())
    A = list(map(int, input().split()))
    s = 0
    d = {}
    d[0] = {0}
    r = 0
    l = [0] * (N + 1)
    for i, v in enumerate(A, start=1):
        if i - K >= 0:
           x = l[i - K]
           d[x].remove(i-K)
        s += v % K
        s %= K
        t = (s - i) % K
        l[i] = t
        if t in d:
            r += len(d[t])
            d[t].add(i)
        else:
            d[t] = {i}
    return r
print(main())
