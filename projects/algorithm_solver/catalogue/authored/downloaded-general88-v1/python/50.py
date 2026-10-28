"""50. Pow(x, n) (Medium).

Specification: https://leetcode.com/problems/powx-n/description/
"""


def solve(x: float, n: int) -> float:
    if n < 0:
        return 1 / solve(x, -n)
    result = 1.0
    base = x
    exponent = n
    while exponent > 0:
        if exponent % 2 == 1:
            result *= base
        base *= base
        exponent //= 2
    return result


class Solution:
    def myPow(self, x: float, n: int) -> float:
        return solve(x, n)
