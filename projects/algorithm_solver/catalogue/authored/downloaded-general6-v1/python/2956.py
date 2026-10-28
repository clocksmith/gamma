"""2956. Find Common Elements Between Two Arrays (Easy).

Specification: https://leetcode.com/problems/find-common-elements-between-two-arrays/description/
"""


def solve(nums1: list[int], nums2: list[int]) -> list[int]:
    set1 = set(nums1)
    set2 = set(nums2)
    count1 = sum(1 for x in nums1 if x in set2)
    count2 = sum(1 for x in nums2 if x in set1)
    return [count1, count2]


class Solution:
    def findIntersectionValues(self, nums1: list[int], nums2: list[int]) -> list[int]:
        return solve(nums1, nums2)
