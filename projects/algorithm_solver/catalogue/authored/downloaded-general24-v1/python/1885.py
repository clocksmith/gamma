"""1885. Count Pairs in Two Arrays (Medium).

Specification: https://leetcode.com/problems/count-pairs-in-two-arrays/description/
"""


def solve(nums1: list[int], nums2: list[int]) -> int:
    diff = sorted(a - b for a, b in zip(nums1, nums2))
    count = 0
    for i in range(len(diff)):
        for j in range(i + 1, len(diff)):
            if diff[i] + diff[j] > 0:
                count += 1
    return count


class Solution:
    def countPairs(self, nums1: list[int], nums2: list[int]) -> int:
        return solve(nums1, nums2)
