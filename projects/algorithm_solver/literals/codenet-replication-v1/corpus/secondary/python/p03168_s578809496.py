n = int(input())
l = list(map(float, input().split()))

dp = [[0]*(n+1) for _ in range(n+1)]
# dp[i][j]: 最初のi枚のコインを投げたとき、表がj枚になる確率
dp[0][0] = 1.0
for i in range(n):
  for j in range(i+1):
    dp[i+1][j+1] += dp[i][j] * l[i]
    dp[i+1][j] += dp[i][j] * (1-l[i])
    
ans_ = 0
for i in range(0, n//2+1):
  ans_ += dp[n][i]
print(1-ans_)