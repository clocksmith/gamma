"""371. Sum of Two Integers (Medium).

Specification: https://leetcode.com/problems/sum-of-two-integers/description/
"""


MASK = 0xFFFFFFFF


def solve(a: int, b: int) -> int:
    x, y = a & MASK, b & MASK
    while y:
        x, y = (x ^ y) & MASK, ((x & y) << 1) & MASK
    return x if x <= 0x7FFFFFFF else ~(x ^ MASK)


class Solution:
    def getSum(self, a: int, b: int) -> int:
        return solve(a, b)
