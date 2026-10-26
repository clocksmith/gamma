"""1636. Sort Array by Increasing Frequency (Easy).

Specification: https://leetcode.com/problems/sort-array-by-increasing-frequency/description/
"""


def solve(nums: list[int]) -> list[int]:
    """O(n log n) time, O(n) space; ascending frequency, then descending numeric value."""
    counts = {}
    for value in nums:
        counts[value] = counts.get(value, 0) + 1
    return sorted(nums, key=lambda value: (counts[value], -value))


class Solution:
    def frequencySort(self, nums: list[int]) -> list[int]:
        return solve(nums)
