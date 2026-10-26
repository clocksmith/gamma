"""219. Contains Duplicate II (Easy).

Specification: https://leetcode.com/problems/contains-duplicate-ii/description/
"""


def solve(nums: list[int], k: int) -> bool:
    """O(n) expected time, O(n) space; retain the most recent index; preserve nums."""
    latest = {}
    for index, value in enumerate(nums):
        if value in latest and index - latest[value] <= k:
            return True
        latest[value] = index
    return False


class Solution:
    def containsNearbyDuplicate(self, nums: list[int], k: int) -> bool:
        return solve(nums, k)
