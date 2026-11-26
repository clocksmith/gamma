H, W, N = map(int, input().split())

Y = [W+100]*(H+1)
P = [[] for i in range(W+1)]
for i in range(N):
    x, y = map(int, input().split())
    if x < y:
        continue
    Y[x-y] = min(Y[x-y], y-1)
    P[y-1].append(x-1)
base = 0
ans = H
for y in range(W):
    while Y[base] == y:
        base += 1
    xmin = y + base
    for x in P[y]:
        if xmin <= x:
            ans = min(x, ans)
print(ans)