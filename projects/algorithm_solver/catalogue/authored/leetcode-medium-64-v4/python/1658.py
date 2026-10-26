"""1658. Minimum Operations to Reduce X to Zero: keep the longest positive-value subarray whose sum is total minus x."""


def solve(nums: list[int], x: int) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    target = sum(nums) - x
    if target < 0:
        return -1
    if target == 0:
        return len(nums)
    left = total = 0
    longest = -1
    for right, value in enumerate(nums):
        total += value
        while total > target:
            total -= nums[left]
            left += 1
        if total == target:
            longest = max(longest, right - left + 1)
    return len(nums) - longest if longest >= 0 else -1


class Solution:
    def minOperations(self, nums: list[int], x: int) -> int:
        return solve(nums, x)
