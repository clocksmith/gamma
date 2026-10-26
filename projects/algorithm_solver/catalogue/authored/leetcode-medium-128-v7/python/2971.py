"""2971. Find Polygon With the Largest Perimeter: take the largest sorted prefix whose previous sides outweigh its largest side."""


def solve(nums: list[int]) -> int:
    """O(n log n) time and O(n) auxiliary space; inputs are read-only."""
    prefix = 0
    best = -1
    for value in sorted(nums):
        if prefix > value:
            best = prefix + value
        prefix += value
    return best


class Solution:
    def largestPerimeter(self, nums: list[int]) -> int:
        return solve(nums)
