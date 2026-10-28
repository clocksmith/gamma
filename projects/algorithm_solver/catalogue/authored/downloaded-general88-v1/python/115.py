"""115. Distinct Subsequences (Hard).

Specification: https://leetcode.com/problems/distinct-subsequences/description/
"""


def solve(s: str, t: str) -> int:
    dp = [0] * (len(t) + 1)
    dp[0] = 1
    for ch in s:
        for j in range(len(t), 0, -1):
            if ch == t[j - 1]:
                dp[j] += dp[j - 1]
    return dp[len(t)]


class Solution:
    def numDistinct(self, s: str, t: str) -> int:
        return solve(s, t)
