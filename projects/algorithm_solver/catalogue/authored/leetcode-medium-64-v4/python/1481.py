"""1481. Least Number of Unique Integers after K Removals: remove complete value groups in ascending frequency order."""
from collections import Counter


def solve(arr: list[int], k: int) -> int:
    """O(n + u log(u + 1)) expected time and O(u) auxiliary space for u distinct values; inputs are read-only."""
    frequencies = sorted(Counter(arr).values())
    remaining = k
    unique = len(frequencies)
    for count in frequencies:
        if count > remaining:
            break
        remaining -= count
        unique -= 1
    return unique


class Solution:
    def findLeastNumOfUniqueInts(self, arr: list[int], k: int) -> int:
        return solve(arr, k)
