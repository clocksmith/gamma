"""3847. Find the Score Difference in a Game."""
from __future__ import annotations


def solve(nums: list[int]) -> int:
    """O(n) time and O(1) space; apply both role changes before awarding each score."""
    active = 1
    answer = 0
    for index, value in enumerate(nums):
        if value % 2:
            active = -active
        if (index + 1) % 6 == 0:
            active = -active
        answer += active * value
    return answer


class Solution:
    def scoreDifference(self, nums: list[int]) -> int:
        return solve(nums)
