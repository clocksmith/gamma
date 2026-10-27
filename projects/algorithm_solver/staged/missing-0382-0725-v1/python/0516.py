"""516. Longest Palindromic Subsequence. Rolling interval dynamic programming; O(n^2) time and O(n) space."""

def solve(s: str) -> int:
    n = len(s)
    if n == 0:
        return 0
    dp = [0] * n
    for left in range(n - 1, -1, -1):
        diagonal = 0
        dp[left] = 1
        for right in range(left + 1, n):
            previous = dp[right]
            if s[left] == s[right]:
                dp[right] = diagonal + 2
            else:
                dp[right] = max(dp[right], dp[right - 1])
            diagonal = previous
    return dp[-1]


class Solution:
    def longestPalindromeSubseq(self, s: str) -> int:
        return solve(s)
