"""3430. Maximum and Minimum Sums of at Most Size K Subarrays: monotonic-stack contributions with a truncated rectangle count."""


def solve(nums: list[int], k: int) -> int:
    """O(n) time and O(n) auxiliary space. Inputs are preserved."""
    n = len(nums)

    def contributions(minimum):
        stack = []
        total = 0
        for right in range(n + 1):
            while stack and (right == n or (nums[stack[-1]] >= nums[right] if minimum else nums[stack[-1]] <= nums[right])):
                middle = stack.pop()
                previous = stack[-1] if stack else -1
                left_choices = min(k, middle - previous)
                right_choices = min(k, right - middle)
                excess = max(0, left_choices + right_choices - k - 1)
                count = left_choices * right_choices - excess * (excess + 1) // 2
                total += nums[middle] * count
            if right < n:
                stack.append(right)
        return total

    return contributions(True) + contributions(False)


class Solution:
    def minMaxSubarraySum(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
