"""172. Factorial Trailing Zeroes (Medium).

Specification: https://leetcode.com/problems/factorial-trailing-zeroes/description/
"""


def solve(n: int) -> int:
    count = 0
    while n > 0:
        n //= 5
        count += n
    return count


class Solution:
    def trailingZeroes(self, n: int) -> int:
        return solve(n)
