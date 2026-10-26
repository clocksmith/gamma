"""3676. Count Bowl Subarrays."""
from __future__ import annotations


def solve(nums: list[int]) -> int:
    """O(n) time and O(n) auxiliary space; inputs are preserved."""
    stack = []
    answer = 0
    for right, value in enumerate(nums):
        while stack and nums[stack[-1]] < value:
            left = stack.pop()
            if right - left >= 2:
                answer += 1
        if stack and right - stack[-1] >= 2:
            answer += 1
        stack.append(right)
    return answer


class Solution:
    def bowlSubarrays(self, nums: list[int]) -> int:
        return solve(nums)
