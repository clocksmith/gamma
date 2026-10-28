"""2605. Form Smallest Number From Two Digit Arrays (Easy).

Specification: https://leetcode.com/problems/form-smallest-number-from-two-digit-arrays/description/
"""


def solve(nums1, nums2):
    common = set(nums1) & set(nums2)
    if common:
        return min(common)
    m1, m2 = min(nums1), min(nums2)
    return min(m1, m2) * 10 + max(m1, m2)


class Solution:
    def minNumber(self, nums1, nums2):
        return solve(nums1, nums2)
