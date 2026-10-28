"""287. Find the Duplicate Number (Medium).

Specification: https://leetcode.com/problems/find-the-duplicate-number/description/
"""


def solve(nums: list[int]) -> int:
    seen = set()
    for value in nums:
        if value in seen:
            return value
        seen.add(value)
    return -1


class Solution:
    def findDuplicate(self, nums: list[int]) -> int:
        return solve(nums)
