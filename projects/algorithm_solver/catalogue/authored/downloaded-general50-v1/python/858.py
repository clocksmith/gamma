"""858. Mirror Reflection (Medium).

Specification: https://leetcode.com/problems/mirror-reflection/description/
"""


import math


def solve(p: int, q: int) -> int:
    lcm = p * q // math.gcd(p, q)
    m = lcm // p
    n = lcm // q
    if m % 2 == 1 and n % 2 == 1:
        return 1
    if m % 2 == 1 and n % 2 == 0:
        return 2
    return 0


class Solution:
    def mirrorReflection(self, p: int, q: int) -> int:
        return solve(p, q)
