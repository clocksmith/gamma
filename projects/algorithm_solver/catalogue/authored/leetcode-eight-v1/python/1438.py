"""Maintain the minimum and maximum of a shrinking sliding window."""
from collections import deque


def solve(nums: list[int], limit: int) -> int:
    """O(n) time and O(n) auxiliary space; the input is read-only."""
    minima, maxima = deque(), deque()
    left = best = 0
    for right, value in enumerate(nums):
        while minima and nums[minima[-1]] > value:
            minima.pop()
        while maxima and nums[maxima[-1]] < value:
            maxima.pop()
        minima.append(right)
        maxima.append(right)
        while nums[maxima[0]] - nums[minima[0]] > limit:
            if minima[0] == left:
                minima.popleft()
            if maxima[0] == left:
                maxima.popleft()
            left += 1
        best = max(best, right - left + 1)
    return best


class Solution:
    def longestSubarray(self, nums: list[int], limit: int) -> int:
        return solve(nums, limit)
