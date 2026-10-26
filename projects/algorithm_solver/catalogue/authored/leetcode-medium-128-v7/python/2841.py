"""2841. Maximum Sum of Almost Unique Subarray: maintain fixed-window sums and the number of distinct values."""


def solve(nums: list[int], m: int, k: int) -> int:
    """O(n) expected time and O(k) auxiliary space; inputs are read-only."""
    counts = {}
    total = best = 0
    for right, value in enumerate(nums):
        total += value
        counts[value] = counts.get(value, 0) + 1
        if right >= k:
            removed = nums[right - k]
            total -= removed
            counts[removed] -= 1
            if counts[removed] == 0:
                del counts[removed]
        if right + 1 >= k and len(counts) >= m:
            best = max(best, total)
    return best


class Solution:
    def maxSum(self, nums: list[int], m: int, k: int) -> int:
        return solve(nums, m, k)
