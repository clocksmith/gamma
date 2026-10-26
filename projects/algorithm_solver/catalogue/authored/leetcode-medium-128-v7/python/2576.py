"""2576. Find the Maximum Number of Marked Indices: pair the smallest values with the first sufficiently large values in the upper half."""


def solve(nums: list[int]) -> int:
    """O(n log n) time and O(n) auxiliary space; inputs are read-only."""
    ordered = sorted(nums)
    small = 0
    for large in range((len(nums) + 1) // 2, len(nums)):
        if 2 * ordered[small] <= ordered[large]:
            small += 1
    return 2 * small


class Solution:
    def maxNumOfMarkedIndices(self, nums: list[int]) -> int:
        return solve(nums)
