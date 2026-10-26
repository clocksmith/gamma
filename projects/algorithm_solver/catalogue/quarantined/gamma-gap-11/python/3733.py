"""3733. Minimum Time to Complete All Deliveries."""
from __future__ import annotations
from math import gcd


def solve(d: list[int], r: list[int]) -> int:
    """O(log(d1 + d2) + log(max r)) time and O(1) space; individual and union capacities characterize feasibility."""
    common = r[0] // gcd(r[0], r[1]) * r[1]
    left, right = 0, 2 * (d[0] + d[1])
    while left < right:
        middle = (left + right) // 2
        feasible = (middle - middle // r[0] >= d[0] and
                    middle - middle // r[1] >= d[1] and
                    middle - middle // common >= d[0] + d[1])
        if feasible:
            right = middle
        else:
            left = middle + 1
    return left


class Solution:
    def minTime(self, d: list[int], r: list[int]) -> int:
        return solve(d, r)
