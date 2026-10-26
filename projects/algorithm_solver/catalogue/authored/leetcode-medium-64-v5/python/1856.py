"""1856. Maximum Subarray Min-Product: use increasing minima and prefix sums to evaluate each maximal span."""


def solve(nums: list[int]) -> int:
    """O(n) time and O(n) auxiliary space on the bounded integer domain; inputs are read-only."""
    prefix = [0]
    for value in nums:
        prefix.append(prefix[-1] + value)
    stack = []
    best = 0
    for right in range(len(nums) + 1):
        value = nums[right] if right < len(nums) else 0
        while stack and nums[stack[-1]] > value:
            minimum = nums[stack.pop()]
            left = stack[-1] + 1 if stack else 0
            best = max(best, minimum * (prefix[right] - prefix[left]))
        if right < len(nums):
            stack.append(right)
    return best % 1_000_000_007


class Solution:
    def maxSumMinProduct(self, nums: list[int]) -> int:
        return solve(nums)
