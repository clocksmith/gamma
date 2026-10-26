"""1748. Sum of Unique Elements (Easy).

Specification: https://leetcode.com/problems/sum-of-unique-elements/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) expected time, O(u) space; sum only values whose final frequency is one."""
    counts = {}
    for value in nums:
        counts[value] = counts.get(value, 0) + 1
    return sum(value for value, count in counts.items() if count == 1)


class Solution:
    def sumOfUnique(self, nums: list[int]) -> int:
        return solve(nums)
