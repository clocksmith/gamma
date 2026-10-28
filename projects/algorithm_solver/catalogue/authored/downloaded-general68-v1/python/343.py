"""343. Integer Break (Medium).

Specification: https://leetcode.com/problems/integer-break/description/
"""


def solve(n: int) -> int:
    if n <= 3:
        return n - 1
    result = 1
    while n > 4:
        result *= 3
        n -= 3
    return result * n


class Solution:
    def integerBreak(self, n: int) -> int:
        return solve(n)
