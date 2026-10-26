"""2091. Removing Minimum and Maximum From Array: compare removing both extremes from either end or splitting the removals."""


def solve(nums: list[int]) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    smallest = largest = 0
    for index, value in enumerate(nums):
        if value < nums[smallest]:
            smallest = index
        if value > nums[largest]:
            largest = index
    left, right = min(smallest, largest), max(smallest, largest)
    return min(right + 1, len(nums) - left, left + 1 + len(nums) - right)


class Solution:
    def minimumDeletions(self, nums: list[int]) -> int:
        return solve(nums)
