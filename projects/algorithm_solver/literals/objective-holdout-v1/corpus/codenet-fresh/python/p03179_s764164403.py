n = int(input())
s = input()
MOD = 10**9 + 7

dp = [[0]*n for i in range(n)]
for i in range(n):
    dp[0][i] = 1

for i in range(n - 1):
    ruiseki = [0] * (n + 1)
    for j in range(n):
        ruiseki[j+1] = ruiseki[j] + dp[i][j]
        ruiseki[j+1] %= MOD

    if s[i] == "<":
        for j in range(n-i-1):
            dp[i+1][j] += ruiseki[n] - ruiseki[j+1]
            dp[i+1][j] %= MOD

    if s[i] == ">":
        for j in range(n-i-1):
            dp[i+1][j] += ruiseki[j+1]
            dp[i+1][j] %= MOD

print(dp[-1][0] % MOD)