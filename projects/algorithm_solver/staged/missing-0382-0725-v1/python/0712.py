"""712. Minimum ASCII Delete Sum for Two Strings."""

def solve(s1: str, s2: str) -> int:
    dp = [0]
    for char in s2:
        dp.append(dp[-1] + ord(char))
    for a in s1:
        diagonal = dp[0]
        dp[0] += ord(a)
        for j, b in enumerate(s2, 1):
            previous = dp[j]
            dp[j] = diagonal if a == b else min(dp[j] + ord(a), dp[j - 1] + ord(b))
            diagonal = previous
    return dp[-1]


class Solution:
    def minimumDeleteSum(self, s1: str, s2: str) -> int:
        return solve(s1, s2)
