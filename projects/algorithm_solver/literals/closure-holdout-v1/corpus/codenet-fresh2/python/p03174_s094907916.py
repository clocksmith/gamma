from itertools import groupby, accumulate, product, permutations, combinations
def solve():
  N = int(input())
  A = [list(map(int, input().split())) for _ in range(N)]
  mod = 10**9+7
  dp = [[0]*(1<<N) for _ in range(N+1)]
  dp[N][0] = 1
  for i in range(N-1,-1,-1):
    for com in combinations(range(N),N-i):
      S = 0
      for k in com:
        S += 1<<k
      for j in com:
        if A[i][j]==1:
          dp[i][S] += dp[i+1][S-(1<<j)]
          dp[i][S] %= mod
  return dp[0][-1]
print(solve())