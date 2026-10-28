"""287. Find the Duplicate Number (Medium).

Specification: https://leetcode.com/problems/find-the-duplicate-number/description/
"""


def solve(nums: list[int]) -> int:
    slow, fast = nums[0], nums[nums[0]]
    while slow != fast:
        slow, fast = nums[slow], nums[nums[fast]]
    entry = 0
    while entry != slow:
        entry, slow = nums[entry], nums[slow]
    return entry


class Solution:
    def findDuplicate(self, nums: list[int]) -> int:
        return solve(nums)
