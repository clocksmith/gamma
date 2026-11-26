N,A = map(int,input().split())
x = list(map(int,input().split()))
X = N*50
dp = [[[0 for i in range(X+1)] for j in range(N+1)] for k in range(N+1)]
dp[0][0][0] = 1
for k in range(1,N+1):
    for j in range(k+1):
        for i in range(j*50+1):
            if i - x[k-1] < 0:
                dp[k][j][i] = dp[k-1][j][i]
            elif k >= 1:
                dp[k][j][i] = dp[k-1][j-1][i-x[k-1]] + dp[k-1][j][i]
ans = 0
for j in range(1,N+1):
    ans += dp[-1][j][j*A]
print(ans)