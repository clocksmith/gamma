while True:
  try:
    n, m = map(int, input().split())
  except EOFError:
    break
  costs = []
  vocals = []
  dances = []
  looks = []
  for _ in range(n):
    input()
    c, v, d, l = map(int, input().split())
    costs.append(c)
    vocals.append(v)
    dances.append(d)
    looks.append(l)
  
  def max_param(params):
    dp = [0] * (m + 1)
    for i in range(n):
      c = costs[i]
      p = params[i]
      for j in range(m - c + 1):
        dp[j + c] = max(dp[j + c], dp[j] + p)
    return dp[-1]

  print(max(max_param(vocals), max_param(dances), max_param(looks)))
  

