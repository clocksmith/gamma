"""2461. Maximum Sum of Distinct Subarrays With Length K: maintain the sum and value frequencies of each complete fixed-width window."""


def solve(nums: list[int], k: int) -> int:
    """O(n) expected time and O(k) auxiliary space; inputs are read-only."""
    counts = {}
    total = best = 0
    for index, value in enumerate(nums):
        counts[value] = counts.get(value, 0) + 1
        total += value
        if index >= k:
            outgoing = nums[index - k]
            total -= outgoing
            counts[outgoing] -= 1
            if counts[outgoing] == 0:
                del counts[outgoing]
        if index >= k - 1 and len(counts) == k:
            best = max(best, total)
    return best


class Solution:
    def maximumSubarraySum(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
