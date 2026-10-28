"""454. 4Sum II (Medium).

Specification: https://leetcode.com/problems/4sum-ii/description/
"""


def solve(nums1: list[int], nums2: list[int], nums3: list[int], nums4: list[int]) -> int:
    sums = {}
    for a in nums1:
        for b in nums2:
            sums[a + b] = sums.get(a + b, 0) + 1
    total = 0
    for c in nums3:
        for d in nums4:
            total += sums.get(-(c + d), 0)
    return total


class Solution:
    def fourSumCount(self, nums1: list[int], nums2: list[int], nums3: list[int], nums4: list[int]) -> int:
        return solve(nums1, nums2, nums3, nums4)
