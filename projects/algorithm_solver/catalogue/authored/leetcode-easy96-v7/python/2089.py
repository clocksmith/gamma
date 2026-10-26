"""2089. Find Target Indices After Sorting Array (Easy).

Specification: https://leetcode.com/problems/find-target-indices-after-sorting-array/description/
"""


def solve(nums: list[int], target: int) -> list[int]:
    """O(n) time, O(r) result space; count smaller and equal values instead of sorting nums."""
    smaller = 0
    equal = 0
    for value in nums:
        if value < target:
            smaller += 1
        elif value == target:
            equal += 1
    return list(range(smaller, smaller + equal))


class Solution:
    def targetIndices(self, nums: list[int], target: int) -> list[int]:
        return solve(nums, target)
