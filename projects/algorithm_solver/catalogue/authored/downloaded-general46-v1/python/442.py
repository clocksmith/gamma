"""442. Find All Duplicates in an Array (Medium).

Specification: https://leetcode.com/problems/find-all-duplicates-in-an-array/description/
"""


def solve(nums: list[int]) -> list[int]:
    counts = {}
    for value in nums:
        counts[value] = counts.get(value, 0) + 1
    return sorted(value for value, count in counts.items() if count == 2)


class Solution:
    def findDuplicates(self, nums: list[int]) -> list[int]:
        return solve(nums)
