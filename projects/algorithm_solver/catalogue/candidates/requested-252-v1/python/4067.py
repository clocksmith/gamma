"""4067. Longest Subarray With Restricted Pair Sums.

Specification: https://leetcode.com/problems/longest-subarray-with-restricted-pair-sums/description/
"""

from __future__ import annotations


def solve(nums: list[int]) -> int:
    """O(n*V) time and O(V) space, V=500; three distinct indices, including repeated values. Inputs are preserved."""
    counts = [0] * 501
    def conflicts(value):
        for first in range(1, 501):
            if counts[first] == 0:
                continue
            if value + first <= 500 and counts[value + first]:
                return True
            second = value - first
            if second >= 1 and counts[second] and (second != first or counts[first] >= 2):
                return True
        return False
    left = answer = 0
    for right, value in enumerate(nums):
        while conflicts(value):
            counts[nums[left]] -= 1
            left += 1
        counts[value] += 1
        answer = max(answer, right - left + 1)
    return answer
