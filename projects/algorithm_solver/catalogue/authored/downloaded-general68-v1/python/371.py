"""371. Sum of Two Integers (Medium).

Specification: https://leetcode.com/problems/sum-of-two-integers/description/
"""


MASK = 0xFFFFFFFF


def solve(a: int, b: int) -> int:
    x, y = a & MASK, b & MASK
    while y != 0:
        carry = ((x & y) << 1) & MASK
        x = (x ^ y) & MASK
        y = carry
    return x if x <= 0x7FFFFFFF else x - 0x100000000


class Solution:
    def getSum(self, a: int, b: int) -> int:
        return solve(a, b)
