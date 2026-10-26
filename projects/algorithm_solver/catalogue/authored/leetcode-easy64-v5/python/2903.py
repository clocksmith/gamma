"""2903. Find Indices With Index and Value Difference I (Easy).

Specification: https://leetcode.com/problems/find-indices-with-index-and-value-difference-i/description/
"""


def solve(nums: list[int], indexDifference: int, valueDifference: int) -> list[int]:
    """O(n) time, O(1) auxiliary space; preserve nums; equal indices are allowed when permitted."""
    minimum_index = 0
    maximum_index = 0
    for right in range(indexDifference, len(nums)):
        candidate = right - indexDifference
        if nums[candidate] < nums[minimum_index]:
            minimum_index = candidate
        if nums[candidate] > nums[maximum_index]:
            maximum_index = candidate
        if abs(nums[right] - nums[minimum_index]) >= valueDifference:
            return [minimum_index, right]
        if abs(nums[right] - nums[maximum_index]) >= valueDifference:
            return [maximum_index, right]
    return [-1, -1]


class Solution:
    def findIndices(self, nums: list[int], indexDifference: int, valueDifference: int) -> list[int]:
        return solve(nums, indexDifference, valueDifference)
