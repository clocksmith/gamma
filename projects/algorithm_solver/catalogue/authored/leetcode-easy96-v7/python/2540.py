"""2540. Minimum Common Value (Easy).

Specification: https://leetcode.com/problems/minimum-common-value/description/
"""


def solve(nums1: list[int], nums2: list[int]) -> int:
    """O(n + m) time, O(1) space; advance the smaller sorted value; preserve both arrays."""
    first = 0
    second = 0
    while first < len(nums1) and second < len(nums2):
        if nums1[first] == nums2[second]:
            return nums1[first]
        if nums1[first] < nums2[second]:
            first += 1
        else:
            second += 1
    return -1


class Solution:
    def getCommon(self, nums1: list[int], nums2: list[int]) -> int:
        return solve(nums1, nums2)
