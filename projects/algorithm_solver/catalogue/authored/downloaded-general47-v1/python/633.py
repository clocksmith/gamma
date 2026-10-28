"""633. Sum of Square Numbers (Medium).

Specification: https://leetcode.com/problems/sum-of-square-numbers/description/
"""


import math


def solve(c: int) -> bool:
    left, right = 0, math.isqrt(c)
    while left <= right:
        total = left * left + right * right
        if total == c:
            return True
        if total < c:
            left += 1
        else:
            right -= 1
    return False


class Solution:
    def judgeSquareSum(self, c: int) -> bool:
        return solve(c)
