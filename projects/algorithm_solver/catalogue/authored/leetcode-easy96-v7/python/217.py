"""217. Contains Duplicate (Easy).

Specification: https://leetcode.com/problems/contains-duplicate/description/
"""


def solve(nums: list[int]) -> bool:
    """O(n) expected time, O(n) space; preserve nums."""
    seen = set()
    for value in nums:
        if value in seen:
            return True
        seen.add(value)
    return False


class Solution:
    def containsDuplicate(self, nums: list[int]) -> bool:
        return solve(nums)
