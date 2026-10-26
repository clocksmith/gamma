"""2104. Sum of Subarray Ranges: count each value as a subarray maximum and minimum with monotonic boundaries."""


def solve(nums: list[int]) -> int:
    """O(n) time and O(n) auxiliary space; inputs are read-only."""
    def contribution(maximum: bool) -> int:
        stack = []
        total = 0
        for right in range(len(nums) + 1):
            while stack and (right == len(nums) or
                             (nums[stack[-1]] < nums[right] if maximum else nums[stack[-1]] > nums[right])):
                index = stack.pop()
                left = stack[-1] if stack else -1
                total += nums[index] * (index - left) * (right - index)
            if right < len(nums):
                stack.append(right)
        return total

    return contribution(True) - contribution(False)


class Solution:
    def subArrayRanges(self, nums: list[int]) -> int:
        return solve(nums)
