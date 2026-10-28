"""326. Power of Three (Easy).

Specification: https://leetcode.com/problems/power-of-three/description/
"""


def solve(n: int) -> bool:
    return n > 0 and 1162261467 % n == 0


class Solution:
    def isPowerOfThree(self, n: int) -> bool:
        return solve(n)
