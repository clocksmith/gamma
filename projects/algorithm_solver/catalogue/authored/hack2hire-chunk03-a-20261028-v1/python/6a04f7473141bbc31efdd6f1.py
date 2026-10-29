"""Hack2Hire 6a04f7473141bbc31efdd6f1 (Kth Greatest in Growing Prefix) over an INFERRED spec; qualification unknown."""
import heapq


def solve(arr, k):
    heap, out = [], []
    for i, value in enumerate(arr):
        if len(heap) < k:
            heapq.heappush(heap, value)
        elif value > heap[0]:
            heapq.heapreplace(heap, value)
        if i + 1 >= k:
            out.append(heap[0])
    return out


class Solution:
    def kthGreatestInPrefixes(self, arr, k):
        return solve(arr, k)
