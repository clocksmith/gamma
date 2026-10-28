"""319. Bulb Switcher (Medium).

Specification: https://leetcode.com/problems/bulb-switcher/description/
"""


import math


def solve(n: int) -> int:
    return math.isqrt(n)


class Solution:
    def bulbSwitch(self, n: int) -> int:
        return solve(n)
