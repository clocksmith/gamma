[H,W] = list(map(int,input().split()))
ls = []
for i in range(H):
  ls.append(input())
dp = [[0 for i in range(W)] for j in range(H)]
for i in range(H):
  for j in range(W):
    if i == 0 and j == 0:
      dp[i][j] = 0
    elif i == 0:
      dp[i][j] = dp[i][j-1] + int(ls[i][j])
    elif j == 0:
      dp[i][j] = dp[i-1][j] + int(ls[i][j])
    else:
      dp[i][j] = min(dp[i-1][j],dp[i][j-1]) + int(ls[i][j])
print(dp[H-1][W-1])