"""471. Encode String with Shortest Length. Interval dynamic programming considers splits and repeated encoded units; ties keep an existing optimum."""

def solve(s: str) -> str:
    n = len(s)
    if n == 0:
        return ''
    dp = [[''] * n for _ in range(n)]
    for length in range(1, n + 1):
        for left in range(n - length + 1):
            right = left + length - 1
            text = s[left:right + 1]
            best = text
            for split in range(left, right):
                candidate = dp[left][split] + dp[split + 1][right]
                if len(candidate) < len(best):
                    best = candidate
            for period in range(1, length // 2 + 1):
                if length % period == 0 and text == text[:period] * (length // period):
                    candidate = str(length // period) + '[' + dp[left][left + period - 1] + ']'
                    if len(candidate) < len(best):
                        best = candidate
            dp[left][right] = best
    return dp[0][n - 1]


class Solution:
    def encode(self, s: str) -> str:
        return solve(s)
