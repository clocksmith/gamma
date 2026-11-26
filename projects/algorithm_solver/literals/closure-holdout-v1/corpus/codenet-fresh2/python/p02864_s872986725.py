import sys
readline = sys.stdin.readline
N, K = map(int, readline().split())
H = list(map(int, readline().split()))
H = [0] + H
N += 1
inf = 10**18
dp = [[[inf]*(K+1) for j in range(N)] for i in range(N)]
dp[0][0][0] = 0
for i in range(1, N):
    hi = H[i]
    for j in range(i):
        hj = H[j]
        for k in range(1, 1 + min(K, i)):
            dp[i][j][k] = dp[i-1][j][k-1]
    for k in range(min(K+1, i)):
        dp[i][i][k] = min(dp[i-1][j][k] + max(0, hi - H[j]) for j in range(i))

print(min(min(dp[N-1][j]) for j in range(N)))