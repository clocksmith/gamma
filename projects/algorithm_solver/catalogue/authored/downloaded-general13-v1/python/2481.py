"""2481. Minimum Cuts to Divide a Circle (Easy).

Specification: https://leetcode.com/problems/minimum-cuts-to-divide-a-circle/description/
"""


def solve(n):
    if n == 1:
        return 0
    return n // 2 if n % 2 == 0 else n


class Solution:
    def numberOfCuts(self, n):
        return solve(n)
