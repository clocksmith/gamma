"""239. Sliding Window Maximum."""
from collections import deque

def solve(nums: list[int], k: int) -> list[int]:
    queue = deque()
    result = []
    for index, value in enumerate(nums):
        while queue and queue[0] <= index - k:
            queue.popleft()
        while queue and nums[queue[-1]] <= value:
            queue.pop()
        queue.append(index)
        if index + 1 >= k:
            result.append(nums[queue[0]])
    return result

class Solution:
    def maxSlidingWindow(self, nums: list[int], k: int) -> list[int]:
        return solve(nums, k)
