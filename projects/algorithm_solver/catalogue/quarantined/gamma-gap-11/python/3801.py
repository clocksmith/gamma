"""3801. Minimum Cost to Merge Sorted Lists."""
from __future__ import annotations


def solve(lists: list[list[int]]) -> int:
    """O(N log N + 2^m * N + 3^m) time and O(N + 2^m) space, m <= 12 and total elements N <= 2000."""
    count = len(lists)
    size = 1 << count
    ordered = sorted((value, index) for index, values in enumerate(lists) for value in values)
    lengths = [0] * size
    medians = [0] * size
    cost = [float('inf')] * size
    cost[0] = 0
    for mask in range(1, size):
        bit = mask & -mask
        index = bit.bit_length() - 1
        lengths[mask] = lengths[mask ^ bit] + len(lists[index])
        position = (lengths[mask] - 1) // 2
        for value, owner in ordered:
            if mask & (1 << owner):
                if position == 0:
                    medians[mask] = value
                    break
                position -= 1
        if mask == bit:
            cost[mask] = 0
            continue
        subset = (mask - 1) & mask
        while subset:
            if subset & bit:
                other = mask ^ subset
                candidate = cost[subset] + cost[other] + lengths[mask] + abs(medians[subset] - medians[other])
                cost[mask] = min(cost[mask], candidate)
            subset = (subset - 1) & mask
    return cost[-1]


class Solution:
    def minMergeCost(self, lists: list[list[int]]) -> int:
        return solve(lists)
