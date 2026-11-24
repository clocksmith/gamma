n = int(input())
res = input()

dic = {"J":0, "O":1, "I":2}
zo = [0,1]
dp =[[[0 for j in zo] for o in zo] for i in zo]

res1 = dic[res[0]]

if res1 == 0:
  for o in zo:
    for i in zo:
      dp[1][o][i] = 1
elif res1 == 1:
  for i in zo:
    dp[1][1][i] = 1
else:
  for o in zo:
    dp[1][o][1] = 1

for d in range(1, n):
  resd = dic[res[d]]
  new = [[[0 for i in zo] for o in zo] for j in zo]
  new[0][0][0] = 0
  new[1][1][1] = sum([dp[x][y][z] for x in zo for y in zo for z in zo])
  new[0][0][1] = sum([dp[x][y][1] for x in zo for y in zo]) if resd == 2 else 0
  new[0][1][0] = sum([dp[x][1][y] for x in zo for y in zo]) if resd == 1 else 0
  new[1][0][0] = sum([dp[1][x][y] for x in [0,1] for y in [0,1]]) if resd == 0 else 0
  new[0][1][1] = sum([dp[x][1][y] + dp[x][y][1] for x in zo for y in zo]) - sum(dp[x][1][1] for x in zo) if resd in [1, 2] else 0
  new[1][0][1] = sum([dp[1][x][y] + dp[x][y][1] for x in zo for y in zo]) - sum(dp[1][x][1] for x in zo) if resd in [0, 2] else 0
  new[1][1][0] = sum([dp[x][1][y] + dp[1][x][y] for x in zo for y in zo]) - sum(dp[1][1][x] for x in zo) if resd in [0, 1] else 0
  dp = new

ans = 0
for i in zo:
  for j in zo:
    for k in zo:
      ans += dp[i][j][k]

print(ans % 10007)
