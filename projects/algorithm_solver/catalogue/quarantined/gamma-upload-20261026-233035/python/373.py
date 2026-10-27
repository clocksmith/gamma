"""373. Find K Pairs with Smallest Sums."""
import heapq

def solve(nums1: list[int], nums2: list[int], k: int) -> list[list[int]]:
    if not nums1 or not nums2 or k == 0:
        return []
    heap = [(nums1[index] + nums2[0], index, 0) for index in range(min(k, len(nums1)))]
    heapq.heapify(heap)
    result = []
    while heap and len(result) < k:
        _, left, right = heapq.heappop(heap)
        result.append([nums1[left], nums2[right]])
        if right + 1 < len(nums2):
            heapq.heappush(heap, (nums1[left] + nums2[right + 1], left, right + 1))
    return result

class Solution:
    def kSmallestPairs(self, nums1, nums2, k):
        return solve(nums1, nums2, k)
