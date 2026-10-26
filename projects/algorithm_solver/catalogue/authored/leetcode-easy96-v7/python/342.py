"""342. Power of Four (Easy).

Specification: https://leetcode.com/problems/power-of-four/description/
"""


def solve(n: int) -> bool:
    """O(log n) time, O(1) space; repeatedly divide by four without floating logarithms."""
    if n <= 0:
        return False
    value = n
    while value % 4 == 0:
        value //= 4
    return value == 1


class Solution:
    def isPowerOfFour(self, n: int) -> bool:
        return solve(n)
