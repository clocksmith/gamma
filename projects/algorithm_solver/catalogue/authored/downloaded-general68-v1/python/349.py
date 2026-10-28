"""349. Intersection of Two Arrays (Easy).

Specification: https://leetcode.com/problems/intersection-of-two-arrays/description/
"""


def solve(nums1: list[int], nums2: list[int]) -> list[int]:
    set2 = set(nums2)
    return sorted({value for value in nums1 if value in set2})


class Solution:
    def intersection(self, nums1: list[int], nums2: list[int]) -> list[int]:
        return solve(nums1, nums2)
