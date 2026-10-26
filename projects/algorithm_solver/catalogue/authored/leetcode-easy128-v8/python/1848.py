"""1848. Minimum Distance to the Target Element (Easy).

Specification: https://leetcode.com/problems/minimum-distance-to-the-target-element/description/
"""


def solve(nums: list[int], target: int, start: int) -> int:
    """O(n) time, O(1) space; the contract guarantees at least one target occurrence."""
    closest = len(nums)
    for index, value in enumerate(nums):
        if value == target:
            closest = min(closest, abs(index - start))
    return closest


class Solution:
    def getMinDistance(self, nums: list[int], target: int, start: int) -> int:
        return solve(nums, target, start)
