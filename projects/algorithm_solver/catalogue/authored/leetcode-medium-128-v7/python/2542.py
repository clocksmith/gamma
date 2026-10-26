"""2542. Maximum Subsequence Score: sweep decreasing minima while retaining the k largest eligible first values."""
from heapq import heappop, heappush


def solve(nums1: list[int], nums2: list[int], k: int) -> int:
    """O(n log n) time and O(n) auxiliary space; inputs are read-only."""
    order = sorted(range(len(nums1)), key=lambda index: nums2[index], reverse=True)
    heap = []
    total = best = 0
    for index in order:
        heappush(heap, nums1[index])
        total += nums1[index]
        if len(heap) > k:
            total -= heappop(heap)
        if len(heap) == k:
            best = max(best, total * nums2[index])
    return best


class Solution:
    def maxScore(self, nums1: list[int], nums2: list[int], k: int) -> int:
        return solve(nums1, nums2, k)
