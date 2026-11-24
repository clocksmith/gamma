from collections import defaultdict as dd

N, X = [int(i) for i in input().split()]
sList = [int(i) for i in input().split()]
sList.sort(reverse=True)
mod = 10 ** 9 + 7

dp = dd(int)
dp[X] = 1
for i, s in enumerate(sList):
    new_dp = dd(int)
    for x in dp:
        new_dp[x] += dp[x] * (N - i - 1)
        new_dp[x] %= mod
        new_dp[x % s] += dp[x]
        new_dp[x % s] %= mod
    dp = new_dp

ans = 0
for x in dp:
    ans += x * dp[x]
    ans %= mod

print(ans)
