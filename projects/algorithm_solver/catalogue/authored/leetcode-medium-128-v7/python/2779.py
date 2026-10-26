"""2779. Maximum Beauty of an Array After Applying Operation: find the largest sorted window whose value range is at most twice k."""


def solve(nums: list[int], k: int) -> int:
    """O(n log n) time and O(n) auxiliary space; inputs are read-only."""
    ordered = sorted(nums)
    left = best = 0
    for right, value in enumerate(ordered):
        while value - ordered[left] > 2 * k:
            left += 1
        best = max(best, right - left + 1)
    return best


class Solution:
    def maximumBeauty(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
