"""Hack2Hire 6a48164d3588ba8acc693047 (Merge Unique Arrays) over an INFERRED spec; qualification unknown."""


def solve(nums1, nums2):
    out = []
    i = j = 0
    while i < len(nums1) or j < len(nums2):
        if j >= len(nums2) or (i < len(nums1) and nums1[i] <= nums2[j]):
            value = nums1[i]
            i += 1
        else:
            value = nums2[j]
            j += 1
        if not out or out[-1] < value:
            out.append(value)
    return out


class Solution:
    def mergeUnique(self, nums1, nums2):
        return solve(nums1, nums2)
