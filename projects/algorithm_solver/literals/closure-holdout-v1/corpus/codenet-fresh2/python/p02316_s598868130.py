N, W = map(int, input().split())
v = [0]*(N+1)
w = [0]*(N+1)
for i in range(1, N+1):
    v[i], w[i] = map(int, input().split())

dp = [[0]*(W+1) for i in range(N+1)]

for i in range(1, N+1):
    for j in range(1, W+1):
        if w[i] > j:
            dp[i][j] = dp[i-1][j]
        else:
            dp[i][j] = max(dp[i-1][j], dp[i][j-w[i]]+v[i], dp[i-1][j-w[i]]+v[i])

print(dp[N][W])