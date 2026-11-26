a, b, c, d = map(int, input().split())
MOD = 998244353


dp = [[0] * (d + 1) for i in range(c + 1)]
dp[a][b] = 1

for i in range(a, c):
    dp[i + 1][b] = b * dp[i][b]
    dp[i + 1][b] %= MOD
for j in range(b, d):
    dp[a][j + 1] = a * dp[a][j]
    dp[a][j + 1] %= MOD
for i in range(a, c):
    for j in range(b, d):
        dp[i + 1][j + 1] = dp[i][j + 1] * (j + 1) + dp[i + 1][j] * (i + 1) - dp[i][j] * (i * j)
        dp[i + 1][j + 1] %= MOD
print(dp[-1][-1])
