"""474. Ones and Zeroes (Medium).

Specification: https://leetcode.com/problems/ones-and-zeroes/description/
"""


def solve(strs: list[str], m: int, n: int) -> int:
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for text in strs:
        zeros = text.count('0')
        ones = text.count('1')
        for z in range(m, zeros - 1, -1):
            for o in range(n, ones - 1, -1):
                dp[z][o] = max(dp[z][o], dp[z - zeros][o - ones] + 1)
    return dp[m][n]


class Solution:
    def findMaxForm(self, strs: list[str], m: int, n: int) -> int:
        return solve(strs, m, n)
