"""Original frontend 730 variant; qualification unknown."""

def solve(s):
    modulus = 10**9 + 7
    n = len(s)
    following = [n] * n
    preceding = [-1] * n
    seen = {}
    for i in range(n - 1, -1, -1):
        following[i] = seen.get(s[i], n)
        seen[s[i]] = i
    seen = {}
    for i in range(n):
        preceding[i] = seen.get(s[i], -1)
        seen[s[i]] = i
    dp = [[0] * (n + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        row, below = dp[i], dp[i + 1]
        row[i] = 1
        for j in range(i + 1, n):
            if s[i] != s[j]:
                value = below[j] + row[j - 1] - below[j - 1]
            else:
                low, high = following[i], preceding[j]
                inner = below[j - 1]
                if low > high:
                    value = 2 * inner + 2
                elif low == high:
                    value = 2 * inner + 1
                else:
                    value = 2 * inner - dp[low + 1][high - 1]
            row[j] = value % modulus
    return dp[0][n - 1]


class Solution:
    def countPalindromicSubsequences(self, s):
        return solve(s)
