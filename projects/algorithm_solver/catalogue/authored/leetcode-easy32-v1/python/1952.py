"""1952. Three Divisors (Easy).

Specification: https://leetcode.com/problems/three-divisors/description/
"""

from math import isqrt


def solve(n: int) -> bool:
    """O(n^(1/4)) time, O(1) space under the bounded integer domain."""
    root = isqrt(n)
    if root < 2 or root * root != n:
        return False
    divisor = 2
    while divisor * divisor <= root:
        if root % divisor == 0:
            return False
        divisor += 1
    return True


class Solution:
    def isThree(self, n: int) -> bool:
        return solve(n)
