"""454. 4Sum II."""

from collections import Counter

def solve(nums1: list[int], nums2: list[int], nums3: list[int], nums4: list[int]) -> int:
    counts = Counter(a + b for a in nums1 for b in nums2)
    return sum(counts[-c - d] for c in nums3 for d in nums4)


class Solution:
    def fourSumCount(self, nums1: list[int], nums2: list[int], nums3: list[int], nums4: list[int]) -> int:
        return solve(nums1, nums2, nums3, nums4)
