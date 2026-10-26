"""1425. Constrained Subsequence Sum: monotonic deque of DP maxima; O(n) time and O(n) space."""

from collections import deque


def solve(nums: list[int], k: int) -> int:
    best = [0] * len(nums)
    queue = deque()
    answer = float('-inf')
    for index, value in enumerate(nums):
        while queue and queue[0] < index - k:
            queue.popleft()
        best[index] = value + max(0, best[queue[0]] if queue else 0)
        answer = max(answer, best[index])
        while queue and best[queue[-1]] <= best[index]:
            queue.pop()
        queue.append(index)
    return answer


class Solution:
    def constrainedSubsetSum(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
