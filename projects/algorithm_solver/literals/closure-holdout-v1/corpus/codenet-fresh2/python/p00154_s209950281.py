while True:
  m = int(input())
  if m == 0:
    break

  nums = []
  for _ in range(m):
    a, b = map(int, input().split())
    lst = [a * i for i in range(b + 1)]
    nums.append(lst)
  
  """
  dp[x][y] ... x種類目まででyを作る場合の数
  dp[x][y] = sum(dp[x - 1][y - wk] for wk in nums[x])
  """
  
  def solve(n):
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
      dp[i][0] = 1
    for x in range(1, m + 1):
      for y in range(1, n + 1):
        dp[x][y] = sum([dp[x - 1][y - v] for v in nums[x - 1] if v <= y])
    print(dp[m][n])
    
  g = int(input())
  for _ in range(g):
    solve(int(input()))
