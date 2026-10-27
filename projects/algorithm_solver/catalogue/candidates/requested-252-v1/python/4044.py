"""4044. Count Good Cyclic Rotations.

Specification: https://leetcode.com/problems/count-good-cyclic-rotations/description/
"""

from __future__ import annotations


def solve(nums: list[int]) -> int:
    """O(n) time and O(1) auxiliary space; first half sum must strictly exceed the second half. Inputs are preserved."""
    half = len(nums) // 2
    total = sum(nums)
    window = sum(nums[index] for index in range(half))
    answer = 0
    for start in range(len(nums)):
        answer += window > total - window
        window += nums[(start + half) % len(nums)] - nums[start]
    return answer
