"""4031. Find All Numbers Disappeared in an Array II.

Specification: https://leetcode.com/problems/find-all-numbers-disappeared-in-an-array-ii/description/
"""

from __future__ import annotations


def solve(nums: list[int], lower: int, upper: int) -> list[list[int]]:
    """O(n log n) time and O(n) space; return maximal inclusive missing ranges. Inputs are preserved."""
    values = sorted({value for value in nums if lower <= value <= upper})
    answer = []
    following = lower
    for value in values:
        if following < value:
            answer.append([following, value - 1])
        following = value + 1
    if following <= upper:
        answer.append([following, upper])
    return answer
