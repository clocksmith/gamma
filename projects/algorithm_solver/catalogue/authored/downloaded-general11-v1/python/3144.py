"""3144. Minimum Substring Partition of Equal Character Frequency (Medium).

Specification: https://leetcode.com/problems/minimum-substring-partition-of-equal-character-frequency/description/
"""


def solve(s: str) -> int:
    n = len(s)
    dp = [10 ** 9] * (n + 1)
    dp[0] = 0
    for end in range(n):
        counts = {}
        for start in range(end, -1, -1):
            counts[s[start]] = counts.get(s[start], 0) + 1
            vals = counts.values()
            if min(vals) == max(vals):
                dp[end + 1] = min(dp[end + 1], dp[start] + 1)
    return dp[n]


class Solution:
    def minimumSubstringsInPartition(self, s):
        return solve(s)
