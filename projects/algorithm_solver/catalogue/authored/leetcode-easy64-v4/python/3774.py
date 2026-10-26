"""3774. Absolute Difference Between Maximum and Minimum K Elements (Easy).

Specification: https://leetcode.com/problems/absolute-difference-between-maximum-and-minimum-k-elements/description/
"""


def solve(nums: list[int], k: int) -> int:
    """O(n log n) time, O(n) space; sort a copy and preserve nums."""
    ordered = sorted(nums)
    difference = 0
    for index in range(k):
        difference += ordered[len(ordered) - 1 - index] - ordered[index]
    return difference


class Solution:
    def absDifference(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
