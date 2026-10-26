"""3046. Split the Array (Easy).

Specification: https://leetcode.com/problems/split-the-array/description/
"""


def solve(nums: list[int]) -> bool:
    """O(n) expected time, O(n) space; an even-length input is splittable iff each count is at most two."""
    counts = {}
    for value in nums:
        count = counts.get(value, 0) + 1
        if count > 2:
            return False
        counts[value] = count
    return True


class Solution:
    def isPossibleToSplit(self, nums: list[int]) -> bool:
        return solve(nums)
