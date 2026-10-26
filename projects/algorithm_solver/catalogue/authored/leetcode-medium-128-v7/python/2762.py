"""2762. Continuous Subarrays: count windows whose monotone-queue maximum and minimum differ by at most two."""
from collections import deque


def solve(nums: list[int]) -> int:
    """O(n) time and O(n) auxiliary space; inputs are read-only."""
    minima, maxima = deque(), deque()
    left = total = 0
    for right, value in enumerate(nums):
        while minima and nums[minima[-1]] > value:
            minima.pop()
        while maxima and nums[maxima[-1]] < value:
            maxima.pop()
        minima.append(right)
        maxima.append(right)
        while nums[maxima[0]] - nums[minima[0]] > 2:
            if minima[0] == left:
                minima.popleft()
            if maxima[0] == left:
                maxima.popleft()
            left += 1
        total += right - left + 1
    return total


class Solution:
    def continuousSubarrays(self, nums: list[int]) -> int:
        return solve(nums)
