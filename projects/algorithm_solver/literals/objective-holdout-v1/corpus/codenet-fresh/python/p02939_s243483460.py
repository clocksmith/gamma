s = input()
l = len(s)

dp = [[0, 0] for _ in range(l+1)]
dp[1][0] = 1

for i in range(2, l+1):
    if s[i-1] != s[i-2]:
        dp[i][0] = dp[i-1][0] + 1

    dp[i][0] = max(dp[i][0], dp[i-1][1] + 1)
    dp[i][1] = dp[i-2][0] + 1
    # print(dp)

print(max(dp[-1]))
