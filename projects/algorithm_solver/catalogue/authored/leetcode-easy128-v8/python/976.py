"""976. Largest Perimeter Triangle (Easy).

Specification: https://leetcode.com/problems/largest-perimeter-triangle/description/
"""


def solve(nums: list[int]) -> int:
    """O(n log n) time, O(n) space; the first valid descending triple has maximum perimeter."""
    values = sorted(nums, reverse=True)
    for index in range(len(values) - 2):
        if values[index] < values[index + 1] + values[index + 2]:
            return values[index] + values[index + 1] + values[index + 2]
    return 0


class Solution:
    def largestPerimeter(self, nums: list[int]) -> int:
        return solve(nums)
