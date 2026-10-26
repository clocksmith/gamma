"""3867. Sum of GCD of Formed Pairs."""
from __future__ import annotations
from math import gcd


def solve(nums: list[int]) -> int:
    """O(n log n + n log M) time and O(n) space; construct prefix-maximum GCDs before pairing extremes."""
    maximum = 0
    values = []
    for value in nums:
        maximum = max(maximum, value)
        values.append(gcd(value, maximum))
    values.sort()
    return sum(gcd(values[index], values[-1 - index]) for index in range(len(values) // 2))


class Solution:
    def gcdSum(self, nums: list[int]) -> int:
        return solve(nums)
