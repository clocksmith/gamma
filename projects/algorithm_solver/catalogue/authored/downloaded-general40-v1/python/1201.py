"""1201. Ugly Number III (Medium).

Specification: https://leetcode.com/problems/ugly-number-iii/description/
"""


import math


def _lcm(a, b):
    return a // math.gcd(a, b) * b


def _count_ugly(n, a, b, c):
    return n // a + n // b + n // c - n // _lcm(a, b) - n // _lcm(b, c) - n // _lcm(a, c) + n // _lcm(a, _lcm(b, c))


def solve(n: int, a: int, b: int, c: int) -> int:
    left, right = 1, 2000000000
    while left < right:
        mid = (left + right) // 2
        if _count_ugly(mid, a, b, c) >= n:
            right = mid
        else:
            left = mid + 1
    return left


class Solution:
    def nthUglyNumber(self, n: int, a: int, b: int, c: int) -> int:
        return solve(n, a, b, c)
