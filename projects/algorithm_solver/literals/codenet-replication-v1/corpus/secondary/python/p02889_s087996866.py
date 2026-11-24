N, M, L = map(int, input().split())

INF = float('inf')
d1 = [[INF]*N for _ in range(N)]


for _ in range(M):
    a, b, c = map(int, input().split())
    a -= 1
    b -= 1
    d1[a][b] = c
    d1[b][a] = c
for i in range(N):
    d1[i][i] = 0
for k in range(N):
    for i in range(N):
        for j in range(N):
            d1[i][j] = min(d1[i][k] + d1[k][j], d1[i][j])

d2 = [[INF]*N for _ in range(N)]

for i in range(N):
    for j in range(N):
        if i == j:
            d2[i][j] = 0
        if d1[i][j] <= L and i != j:
            d2[i][j] = 1
for k in range(N):
    for i in range(N):
        for j in range(N):
            d2[i][j] = min(d2[i][k] + d2[k][j], d2[i][j])
Q = int(input())
for _ in range(Q):
    s, t = map(int, input().split())
    s -= 1
    t -= 1
    if d2[s][t] == INF:
        print(-1)
    else:
        print(d2[s][t]-1)
