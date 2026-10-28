"""878. Nth Magical Number (Hard).

Specification: https://leetcode.com/problems/nth-magical-number/description/
"""


import math


def solve(n: int, a: int, b: int) -> int:
    MOD = 1000000007
    lcm = a * b // math.gcd(a, b)
    lo, hi = 1, n * min(a, b)
    while lo < hi:
        mid = (lo + hi) // 2
        count = mid // a + mid // b - mid // lcm
        if count >= n:
            hi = mid
        else:
            lo = mid + 1
    return lo % MOD


class Solution:
    def nthMagicalNumber(self, n: int, a: int, b: int) -> int:
        return solve(n, a, b)
