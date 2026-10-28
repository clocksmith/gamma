"""75. Sort Colors (Medium).

Specification: https://leetcode.com/problems/sort-colors/description/
"""


def solve(nums: list[int]) -> list[int]:
    counts = [0, 0, 0]
    for value in nums:
        counts[value] += 1
    result = []
    for color in range(3):
        result.extend([color] * counts[color])
    return result


class Solution:
    def sortColors(self, nums: list[int]) -> list[int]:
        return solve(nums)
