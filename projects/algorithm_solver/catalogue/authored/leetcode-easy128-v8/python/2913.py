"""2913. Subarrays Distinct Element Sum of Squares I (Easy).

Specification: https://leetcode.com/problems/subarrays-distinct-element-sum-of-squares-i/description/
"""


def solve(nums: list[int]) -> int:
    """O(n^2) expected time, O(n) auxiliary space; extend every start while maintaining distinct values."""
    total = 0
    for start in range(len(nums)):
        distinct = set()
        for end in range(start, len(nums)):
            distinct.add(nums[end])
            total += len(distinct) * len(distinct)
    return total


class Solution:
    def sumCounts(self, nums: list[int]) -> int:
        return solve(nums)
