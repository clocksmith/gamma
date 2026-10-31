"""Original frontend 3316 variant; qualification unknown."""


def solve(source: str, pattern: str, targetIndices) -> int:
    m = len(pattern)
    tset = set(targetIndices)
    NEG = -(10**9)
    dp = [NEG] * (m + 1)
    dp[0] = 0
    for i, ch in enumerate(source):
        in_t = 1 if i in tset else 0
        for j in range(m, 0, -1):
            if dp[j] != NEG:
                dp[j] += in_t
            if ch == pattern[j - 1] and dp[j - 1] != NEG and dp[j - 1] > dp[j]:
                dp[j] = dp[j - 1]
        dp[0] += in_t
    return dp[m]


maxRemovals = solve


class Solution:
    def maxRemovals(self, source: str, pattern: str, targetIndices) -> int:
        return solve(source, pattern, targetIndices)
