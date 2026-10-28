"""2430. Maximum Deletions on a String (Hard).

Specification: https://leetcode.com/problems/maximum-deletions-on-a-string/description/
"""


def solve(s):
    n = len(s)
    dp = [0] * (n + 1)
    for i in range(n - 1, -1, -1):
        dp[i] = 1
        for length in range(1, (n - i) // 2 + 1):
            if s[i:i + length] == s[i + length:i + 2 * length]:
                dp[i] = max(dp[i], 1 + dp[i + length])
    return dp[0]


class Solution:
    def deleteString(self, s):
        return solve(s)
