while True:
    n, m = int(input()), int(input())
    if m == 0:
        break
    d = {k+1:[] for k,_ in enumerate(range(m))}
    for _ in range(m):
        a, b = map(int, input().split())
        d[a].append(b)
        d[b].append(a)
    ans = d[1].copy()
    for k in d[1]:
        ans += d[k]
    print(len(set(ans))-1)