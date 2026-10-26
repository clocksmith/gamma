"""1509. Minimum Difference Between Largest and Smallest Value in Three Moves: compare the four ways to remove three sorted extremes."""


def solve(nums: list[int]) -> int:
    """O(n log n) time and O(n) auxiliary space; inputs are read-only."""
    if len(nums) <= 4:
        return 0
    ordered = sorted(nums)
    return min(ordered[len(nums) - 4 + left] - ordered[left] for left in range(4))


class Solution:
    def minDifference(self, nums: list[int]) -> int:
        return solve(nums)
