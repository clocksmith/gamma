"""2958. Length of Longest Subarray With at Most K Frequency: shrink only until the newly added value meets the frequency limit."""


def solve(nums: list[int], k: int) -> int:
    """O(n) expected time and O(n) auxiliary space; inputs are read-only."""
    counts = {}
    left = best = 0
    for right, value in enumerate(nums):
        counts[value] = counts.get(value, 0) + 1
        while counts[value] > k:
            removed = nums[left]
            counts[removed] -= 1
            left += 1
        best = max(best, right - left + 1)
    return best


class Solution:
    def maxSubarrayLength(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
