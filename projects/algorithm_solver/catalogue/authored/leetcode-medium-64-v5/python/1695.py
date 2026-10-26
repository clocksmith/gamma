"""1695. Maximum Erasure Value: maintain a positive-sum window containing distinct values."""


def solve(nums: list[int]) -> int:
    """O(n) expected time and O(n) auxiliary space; inputs are read-only."""
    seen = set()
    left = total = best = 0
    for value in nums:
        while value in seen:
            removed = nums[left]
            seen.remove(removed)
            total -= removed
            left += 1
        seen.add(value)
        total += value
        best = max(best, total)
    return best


class Solution:
    def maximumUniqueSubarray(self, nums: list[int]) -> int:
        return solve(nums)
