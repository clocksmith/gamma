"""1874. Minimize Product Sum of Two Arrays (Medium).

Specification: https://leetcode.com/problems/minimize-product-sum-of-two-arrays/description/
"""


def solve(nums1: list[int], nums2: list[int]) -> int:
    ascending = sorted(nums1)
    descending = sorted(nums2, reverse=True)
    total = 0
    for i in range(len(ascending)):
        total += ascending[i] * descending[i]
    return total


class Solution:
    def minProductSum(self, nums1: list[int], nums2: list[int]) -> int:
        return solve(nums1, nums2)
