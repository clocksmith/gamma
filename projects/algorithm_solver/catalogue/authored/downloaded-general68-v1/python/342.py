"""342. Power of Four (Easy).

Specification: https://leetcode.com/problems/power-of-four/description/
"""


def solve(n: int) -> bool:
    return n > 0 and (n & (n - 1)) == 0 and (n - 1) % 3 == 0


class Solution:
    def isPowerOfFour(self, n: int) -> bool:
        return solve(n)
