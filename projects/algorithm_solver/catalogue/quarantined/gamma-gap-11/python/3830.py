"""3830. Longest Alternating Subarray After Removing At Most One Element."""
from __future__ import annotations


def solve(nums: list[int]) -> int:
    """O(n) time and space; join compatible alternating runs across each possible removed element."""
    n = len(nums)
    signs = [(nums[index + 1] > nums[index]) - (nums[index + 1] < nums[index]) for index in range(n - 1)]
    left = [1] * n
    right = [1] * n
    for index in range(1, n):
        if signs[index - 1]:
            left[index] = left[index - 1] + 1 if index > 1 and signs[index - 2] == -signs[index - 1] else 2
    for index in range(n - 2, -1, -1):
        if signs[index]:
            right[index] = right[index + 1] + 1 if index + 1 < n - 1 and signs[index + 1] == -signs[index] else 2
    answer = max(left)
    for index in range(1, n - 1):
        bridge = (nums[index + 1] > nums[index - 1]) - (nums[index + 1] < nums[index - 1])
        if bridge == 0:
            continue
        before = left[index - 1]
        after = right[index + 1]
        if before > 1 and signs[index - 2] == bridge:
            before = 1
        if after > 1 and signs[index + 1] == bridge:
            after = 1
        answer = max(answer, before + after)
    return answer


class Solution:
    def longestAlternating(self, nums: list[int]) -> int:
        return solve(nums)
