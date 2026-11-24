n, m = map(int, input().split())
adjList = [[0] * n for _ in range(n)]
for _ in range(m):
    a, b = map(int, input().split())
    a -= 1
    b -= 1
    adjList[a][b] = 1
    adjList[b][a] = 1
def applyComp(a):
    for i in range(len(a)):
        for j in range(len(a[i])):
            a[i][j] = 1 - a[i][j]
applyComp(adjList)

visited = [0] * n
def dfs(u, parent=-1, color=1):
    if visited[u]:
        if visited[u] != color:
            print(-1)
            exit()
        return 0, 0
    visited[u] = color
    oneCount = 0
    twoCount = 0
    if color == 1:
        oneCount += 1
    else:
        twoCount += 1
    for v in range(n):
        if u == v or u == parent:
            continue
        if adjList[u][v]:
            p = dfs(v, u, 3 - color)
            oneCount += p[0]
            twoCount += p[1]
    return oneCount, twoCount
connSize = []
for i in range(n):
    if visited[i]:
        continue
    connSize.append(dfs(i))
dp = [False] * (n + 1)
dp[0] = True
for c1, c2 in connSize:
    ndp = [False] * (n + 1)
    for i in range(n + 1):
        if dp[i]:
            ndp[i+c1] = True
            ndp[i+c2] = True
    dp = ndp
print(min(sum(sz * (sz - 1) // 2 for sz in [sz1, n - sz1]) for sz1 in range(n+1) if dp[sz1]))