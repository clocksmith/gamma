"""2134. Minimum Swaps to Group All 1's Together II: maximize ones in a circular window whose width is the total one count."""


def solve(nums: list[int]) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    width = sum(nums)
    if width <= 1:
        return 0
    inside = 0
    for index in range(width):
        inside += nums[index]
    best = inside
    for start in range(1, len(nums)):
        inside -= nums[start - 1]
        inside += nums[(start + width - 1) % len(nums)]
        best = max(best, inside)
    return width - best


class Solution:
    def minSwaps(self, nums: list[int]) -> int:
        return solve(nums)
