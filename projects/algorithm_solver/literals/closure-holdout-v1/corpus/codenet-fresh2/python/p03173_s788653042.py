import sys
input = sys.stdin.readline
sys.setrecursionlimit(10**7)
from itertools import accumulate
n = int(input())
A = [0] + list(map(int, input().split()))
B = tuple(accumulate(A))
dp = [[-1]*(n+1) for _ in range(n+1)]
def f(i, j):
  if i == j:
    return 0
  if dp[i][j] != -1:
    return dp[i][j]
  if j-i == 1:
    dp[i][j] = A[i]+A[j]
    return dp[i][j]
  res = float("inf")
  for m in range(i, j):
    res = min(res, f(i,m)+f(m+1,j)+(B[j]-B[i-1]))
  dp[i][j] = res
  return res
ans = f(1, n)
print(ans)