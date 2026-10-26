"""3131. Find the Integer Added to Array I (Easy).

Specification: https://leetcode.com/problems/find-the-integer-added-to-array-i/description/
"""


def solve(nums1: list[int], nums2: list[int]) -> int:
    """O(n) time, O(1) auxiliary space; a valid uniform shift is guaranteed; preserve inputs."""
    return min(nums2) - min(nums1)


class Solution:
    def addedInteger(self, nums1: list[int], nums2: list[int]) -> int:
        return solve(nums1, nums2)
