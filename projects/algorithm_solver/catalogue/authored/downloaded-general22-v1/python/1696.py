"""1696. Jump Game VI (Medium).

Specification: https://leetcode.com/problems/jump-game-vi/description/
"""


from collections import deque


def solve(nums: list[int], k: int) -> int:
    dp = [0] * len(nums)
    dp[0] = nums[0]
    queue = deque([0])
    for i in range(1, len(nums)):
        while queue and queue[0] < i - k:
            queue.popleft()
        dp[i] = nums[i] + dp[queue[0]]
        while queue and dp[queue[-1]] <= dp[i]:
            queue.pop()
        queue.append(i)
    return dp[-1]


class Solution:
    def maxResult(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
