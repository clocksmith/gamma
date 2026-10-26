"""2334. Subarray With Elements Greater Than Varying Threshold."""


def solve(nums: list[int], threshold: int) -> int:
    """Monotonic stack of minimum spans; O(n) time and O(n) space. Inputs are preserved."""
    stack = []
    for right in range(len(nums) + 1):
        while stack and (right == len(nums) or nums[stack[-1]] >= nums[right]):
            minimum = nums[stack.pop()]
            left = stack[-1] if stack else -1
            length = right - left - 1
            if minimum * length > threshold:
                return length
        if right < len(nums):
            stack.append(right)
    return -1


class Solution:
    def validSubarraySize(self, nums: list[int], threshold: int) -> int:
        return solve(nums, threshold)
