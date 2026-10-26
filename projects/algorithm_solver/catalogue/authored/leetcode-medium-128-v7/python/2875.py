"""2875. Minimum Size Subarray in Infinite Array: remove complete positive-sum periods and find the shortest circular remainder window."""


def solve(nums: list[int], target: int) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    period = sum(nums)
    cycles, remainder = divmod(target, period)
    base = cycles * len(nums)
    if remainder == 0:
        return base
    left = total = 0
    best = len(nums) + 1
    for right in range(2 * len(nums)):
        total += nums[right % len(nums)]
        while total > remainder:
            total -= nums[left % len(nums)]
            left += 1
        if total == remainder:
            best = min(best, right - left + 1)
    return base + best if best <= len(nums) else -1


class Solution:
    def minSizeSubarray(self, nums: list[int], target: int) -> int:
        return solve(nums, target)
