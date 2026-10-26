"""3741. Minimum Distance Between Three Equal Elements II."""
from __future__ import annotations


def solve(nums: list[int]) -> int:
    """O(n) expected time and O(n) space; the best triple consists of consecutive occurrences."""
    recent = {}
    answer = float('inf')
    for index, value in enumerate(nums):
        first, second = recent.get(value, (-1, -1))
        if first >= 0:
            answer = min(answer, 2 * (index - first))
        recent[value] = (second, index)
    return -1 if answer == float('inf') else answer


class Solution:
    def minimumDistance(self, nums: list[int]) -> int:
        return solve(nums)
