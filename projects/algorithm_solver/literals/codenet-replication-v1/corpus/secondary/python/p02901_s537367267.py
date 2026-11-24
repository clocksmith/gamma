import sys
readline = sys.stdin.readline
sys.setrecursionlimit(10**8)
mod = 10**9+7
#mod = 998244353
INF = 10**18
eps = 10**-7

N,M = map(int,readline().split())
dp = [[INF]*(2**N) for i in range(M+1)]
dp[0][0] = 0

for i in range(M):
    a,b = map(int,readline().split())
    c = list(map(int,readline().split()))
    d = sum(2**(ci-1) for ci in c)
    for j in range(2**N):
        dp[i+1][j] = min(dp[i][j],dp[i+1][j])
        dp[i+1][j|d] = min(dp[i][j|d],dp[i][j]+a,dp[i+1][j|d])

print(dp[M][2**N-1] if dp[M][2**N-1] != INF else -1)
