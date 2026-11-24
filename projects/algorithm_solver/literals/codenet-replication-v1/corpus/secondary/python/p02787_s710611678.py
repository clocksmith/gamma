h, n = map(int, input().split())
dp = [[0] * (h+1) for i in range(n)]
a, b = map(int, input().split())
for c in range(1, h+1):
  dp[0][c] = b * ((c-1) // a + 1)
for i in range(1, n):
  a, b = map(int, input().split())
  for c in range(1, h+1):
    opt1 = dp[i-1][c]
    opt2 = dp[i-1][max(0, c-a)] + b
    opt3 = dp[i][max(0, c-a)] + b
    dp[i][c] = min(opt1, opt2, opt3)
print(dp[-1][-1])