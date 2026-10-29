"""Original LeetCode 664 candidate; qualification unknown."""

def solve(s):
    chars = []
    for c in s:
        if not chars or c != chars[-1]: chars.append(c)
    n = len(chars); dp = [[0] * n for _ in range(n)]
    for left in range(n - 1, -1, -1):
        dp[left][left] = 1
        for right in range(left + 1, n):
            dp[left][right] = 1 + dp[left + 1][right]
            for middle in range(left + 1, right + 1):
                if chars[middle] == chars[left]:
                    dp[left][right] = min(dp[left][right], (dp[left + 1][middle - 1] if middle > left + 1 else 0) + dp[middle][right])
    return dp[0][-1]


class Solution:
    def strangePrinter(self, s):
        return solve(s)
