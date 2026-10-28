"""373. Find K Pairs with Smallest Sums (Medium).

Specification: https://leetcode.com/problems/find-k-pairs-with-smallest-sums/description/
"""


def solve(nums1: list[int], nums2: list[int], k: int) -> list[list[int]]:
    pairs = [[a, b] for a in nums1 for b in nums2]
    pairs.sort(key=lambda pair: (pair[0] + pair[1], pair[0], pair[1]))
    return pairs[:k]


class Solution:
    def kSmallestPairs(self, nums1: list[int], nums2: list[int], k: int) -> list[list[int]]:
        return solve(nums1, nums2, k)
