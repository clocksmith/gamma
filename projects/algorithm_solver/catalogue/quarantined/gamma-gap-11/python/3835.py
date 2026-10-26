"""3835. Count Subarrays With Cost Less Than or Equal to K."""
from __future__ import annotations
from collections import deque


def solve(nums: list[int], k: int) -> int:
    """O(n) time and O(n) space; monotone extrema queues and a shrinking valid window."""
    minimum = deque()
    maximum = deque()
    left = 0
    answer = 0
    for right, value in enumerate(nums):
        while minimum and nums[minimum[-1]] >= value:
            minimum.pop()
        while maximum and nums[maximum[-1]] <= value:
            maximum.pop()
        minimum.append(right)
        maximum.append(right)
        while (nums[maximum[0]] - nums[minimum[0]]) * (right - left + 1) > k:
            if minimum[0] == left:
                minimum.popleft()
            if maximum[0] == left:
                maximum.popleft()
            left += 1
        answer += right - left + 1
    return answer


class Solution:
    def countSubarrays(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
