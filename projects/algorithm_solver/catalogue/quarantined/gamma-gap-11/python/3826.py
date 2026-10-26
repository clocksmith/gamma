"""3826. Minimum Partition Score."""
from __future__ import annotations


def solve(nums: list[int], k: int) -> int:
    """O(k n log n) time and O(n) space; convex positive-prefix costs give monotone optimal split positions."""
    n = len(nums)
    prefix = [0]
    for value in nums:
        prefix.append(prefix[-1] + value)
    previous = [float('inf')] * (n + 1)
    previous[0] = 0
    for groups in range(1, k + 1):
        current = [float('inf')] * (n + 1)
        def compute(left, right, first, last):
            if left > right:
                return
            middle = (left + right) // 2
            best = float('inf')
            split = first
            for index in range(first, min(last, middle - 1) + 1):
                total = prefix[middle] - prefix[index]
                value = previous[index] + total * (total + 1) // 2
                if value < best:
                    best, split = value, index
            current[middle] = best
            compute(left, middle - 1, first, split)
            compute(middle + 1, right, split, last)
        compute(groups, n, groups - 1, n - 1)
        previous = current
    return previous[n]


class Solution:
    def minPartitionScore(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
