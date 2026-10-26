"""3834. Merge Adjacent Equal Elements."""
from __future__ import annotations


def solve(nums: list[int]) -> list[int]:
    """O(n) time and space; stack reductions implement leftmost-first merging without mutating inputs."""
    stack = []
    for value in nums:
        while stack and stack[-1] == value:
            value += stack.pop()
        stack.append(value)
    return stack


class Solution:
    def mergeAdjacent(self, nums: list[int]) -> list[int]:
        return solve(nums)
