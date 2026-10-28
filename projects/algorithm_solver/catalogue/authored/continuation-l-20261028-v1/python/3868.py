"""Original frontend 3868 variant; qualification unknown."""

def solve(nums1, nums2):
    from collections import Counter
    first, second = Counter(nums1), Counter(nums2)
    excess = 0
    for value in first.keys() | second.keys():
        total = first[value] + second[value]
        if total % 2:
            return -1
        excess += max(0, first[value] - total // 2)
    return excess


class Solution:
    def minCost(self, nums1, nums2):
        return solve(nums1, nums2)
