"""1745. Palindrome Partitioning IV (Hard).

Specification: https://leetcode.com/problems/palindrome-partitioning-iv/description/
"""


def solve(s: str) -> bool:
    n = len(s)
    pal = [[False] * n for _ in range(n)]
    for i in range(n - 1, -1, -1):
        for j in range(i, n):
            pal[i][j] = s[i] == s[j] and (j - i < 2 or pal[i + 1][j - 1])
    for i in range(n - 2):
        if not pal[0][i]:
            continue
        for j in range(i + 1, n - 1):
            if pal[i + 1][j] and pal[j + 1][n - 1]:
                return True
    return False


class Solution:
    def checkPartitioning(self, s: str) -> bool:
        return solve(s)
