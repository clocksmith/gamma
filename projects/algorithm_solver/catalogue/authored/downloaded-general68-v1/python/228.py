"""228. Summary Ranges (Easy).

Specification: https://leetcode.com/problems/summary-ranges/description/
"""


def solve(nums: list[int]) -> list[str]:
    result = []
    start = 0
    for i, value in enumerate(nums):
        if i + 1 == len(nums) or nums[i + 1] != value + 1:
            result.append(str(nums[start]) if start == i else f"{nums[start]}->{value}")
            start = i + 1
    return result


class Solution:
    def summaryRanges(self, nums: list[int]) -> list[str]:
        return solve(nums)
