"""3768. Minimum Inversion Count in Subarrays of Fixed Length."""
from __future__ import annotations


def solve(nums: list[int], k: int) -> int:
    """O(n log n) time and O(n) space; sliding Fenwick counts exclude equal values from inversions."""
    values = sorted(set(nums))
    rank = {value: index + 1 for index, value in enumerate(values)}
    tree = [0] * (len(values) + 1)
    def update(index, delta):
        while index < len(tree):
            tree[index] += delta
            index += index & -index
    def prefix(index):
        total = 0
        while index:
            total += tree[index]
            index -= index & -index
        return total
    inversions = 0
    answer = float('inf')
    size = 0
    for index, value in enumerate(nums):
        if index >= k:
            old = rank[nums[index - k]]
            inversions -= prefix(old - 1)
            update(old, -1)
            size -= 1
        position = rank[value]
        inversions += size - prefix(position)
        update(position, 1)
        size += 1
        if size == k:
            answer = min(answer, inversions)
    return answer


class Solution:
    def minInversionCount(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
