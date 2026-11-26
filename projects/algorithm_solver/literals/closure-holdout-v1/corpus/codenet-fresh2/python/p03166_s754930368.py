from collections import deque
N, M = map(int, input().split())
X = [[] for i in range(N)] # iからの行き先
Y = [0 for i in range(N)] # iに来る辺の数
dp = [0 for i in range(N)] # iで終わる最長経路の長さ

for i in range(M):
    x, y = map(int, input().split())
    x -= 1
    y -= 1
    X[x].append(y)
    Y[y] += 1


Q = deque([])
for i in range(N):
    if Y[i] == 0:
        Q.append(i)

while len(Q) > 0:
    i = Q.popleft()
    for x in X[i]:
        dp[x] = max(dp[x], dp[i] + 1)
        Y[x] -= 1
        if Y[x] == 0:
            Q.append(x)

print(max(dp))