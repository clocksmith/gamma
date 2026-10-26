"""2436. Minimum Split Into Subarrays With GCD Greater Than One: extend each part until its running gcd would become one."""
from math import gcd


def solve(nums: list[int]) -> int:
    """O(n log M) time and O(1) auxiliary space for maximum value M; inputs are read-only."""
    parts = 1
    current = 0
    for value in nums:
        merged = gcd(current, value)
        if merged == 1:
            parts += 1
            current = value
        else:
            current = merged
    return parts


class Solution:
    def minimumSplits(self, nums: list[int]) -> int:
        return solve(nums)
