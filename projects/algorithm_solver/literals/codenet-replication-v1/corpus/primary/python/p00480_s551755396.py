N = int(input())
a = list(map(int, input().split()))

## dp[i][j]: i???????????°????????§??§j????????????????????°
dp = [[0 for j in range(21)] for i in range(N-1)]

dp[0][a[0]] = 1
for i in range(1, N-1):
    for j in range(21):
        if (j - a[i]) in range(21):
            dp[i][j] += dp[i-1][j-a[i]]
        if (j + a[i]) in range(21):
            dp[i][j] += dp[i-1][j+a[i]]
        
print(dp[N-2][a[N-1]])