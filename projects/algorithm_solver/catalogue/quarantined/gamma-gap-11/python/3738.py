"""3738. Longest Non-Decreasing Subarray After Replacing at Most One Element."""
from __future__ import annotations


def solve(nums: list[int]) -> int:
    """O(n) time and O(n) space; bridge adjacent monotone runs only when one replacement can join them."""
    n = len(nums)
    left = [1] * n
    right = [1] * n
    for index in range(1, n):
        if nums[index - 1] <= nums[index]:
            left[index] = left[index - 1] + 1
    for index in range(n - 2, -1, -1):
        if nums[index] <= nums[index + 1]:
            right[index] = right[index + 1] + 1
    answer = max(left)
    for index in range(n):
        before = left[index - 1] if index else 0
        after = right[index + 1] if index + 1 < n else 0
        answer = max(answer, before + 1, after + 1)
        if index and index + 1 < n and nums[index - 1] <= nums[index + 1]:
            answer = max(answer, before + after + 1)
    return answer


class Solution:
    def longestSubarray(self, nums: list[int]) -> int:
        return solve(nums)
