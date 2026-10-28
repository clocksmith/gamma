"""2327. Number of People Aware of a Secret (Medium).

Specification: https://leetcode.com/problems/number-of-people-aware-of-a-secret/description/
"""


def solve(n: int, delay: int, forget: int) -> int:
    MOD = 1000000007
    dp = [0] * (n + 1)
    dp[1] = 1
    window = 0
    for day in range(2, n + 1):
        if day - delay >= 1:
            window = (window + dp[day - delay]) % MOD
        if day - forget >= 1:
            window = (window - dp[day - forget]) % MOD
        dp[day] = window
    ans = 0
    for day in range(n - forget + 1, n + 1):
        if day >= 1:
            ans = (ans + dp[day]) % MOD
    return ans


class Solution:
    def peopleAwareOfSecret(self, n, delay, forget) -> object:
        return solve(n, delay, forget)
