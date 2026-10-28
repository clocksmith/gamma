"""88. Merge Sorted Array (Easy).

Specification: https://leetcode.com/problems/merge-sorted-array/description/
"""


def solve(nums1: list[int], m: int, nums2: list[int], n: int) -> list[int]:
    return sorted(nums1[:m] + nums2[:n])


class Solution:
    def merge(self, nums1: list[int], m: int, nums2: list[int], n: int) -> list[int]:
        return solve(nums1, m, nums2, n)
