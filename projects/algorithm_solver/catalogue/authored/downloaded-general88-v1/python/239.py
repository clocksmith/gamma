"""239. Sliding Window Maximum (Hard).

Specification: https://leetcode.com/problems/sliding-window-maximum/description/
"""


def solve(nums: list[int], k: int) -> list[int]:
    from collections import deque
    queue = deque()
    result = []
    for i, value in enumerate(nums):
        while queue and queue[0] <= i - k:
            queue.popleft()
        while queue and nums[queue[-1]] <= value:
            queue.pop()
        queue.append(i)
        if i >= k - 1:
            result.append(nums[queue[0]])
    return result


class Solution:
    def maxSlidingWindow(self, nums: list[int], k: int) -> list[int]:
        return solve(nums, k)
