"""3859. Count Subarrays With K Distinct Integers."""
from __future__ import annotations
from heapq import heappop, heappush


def solve(nums: list[int], k: int, m: int) -> int:
    """O(n log n) time and O(n) space; at-most-k window and the minimum mth-last occurrence among its active values."""
    occurrences = {}
    active = {}
    latest = {}
    heap = []
    left = 0
    answer = 0
    for right, value in enumerate(nums):
        positions = occurrences.setdefault(value, [])
        positions.append(right)
        latest[value] = right
        active[value] = active.get(value, 0) + 1
        while len(active) > k:
            dropped = nums[left]
            active[dropped] -= 1
            if active[dropped] == 0:
                del active[dropped]
            left += 1
        boundary = positions[-m] if len(positions) >= m else -1
        heappush(heap, (boundary, value, right))
        while heap and (heap[0][1] not in active or latest[heap[0][1]] != heap[0][2]):
            heappop(heap)
        if len(active) == k:
            answer += max(0, heap[0][0] - left + 1)
    return answer


class Solution:
    def countSubarrays(self, nums: list[int], k: int, m: int) -> int:
        return solve(nums, k, m)
