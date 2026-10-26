"""3092. Most Frequent IDs: keep current counts and discard outdated maximum-heap records lazily."""
from heapq import heappop, heappush


def solve(nums: list[int], freq: list[int]) -> list[int]:
    """O(n log n) time and O(n) auxiliary space; inputs are read-only."""
    counts = {}
    heap = []
    result = []
    for identity, change in zip(nums, freq):
        current = counts.get(identity, 0) + change
        counts[identity] = current
        heappush(heap, (-current, identity))
        while heap and -heap[0][0] != counts[heap[0][1]]:
            heappop(heap)
        result.append(-heap[0][0] if heap else 0)
    return result


class Solution:
    def mostFrequentIDs(self, nums: list[int], freq: list[int]) -> list[int]:
        return solve(nums, freq)
