"""1338. Reduce Array Size to The Half: remove the most frequent values first."""
from collections import Counter


def solve(arr: list[int]) -> int:
    """O(n + u log u) time and O(u) auxiliary space for u distinct values; inputs are read-only."""
    frequencies = sorted(Counter(arr).values(), reverse=True)
    removed = 0
    for chosen, frequency in enumerate(frequencies, 1):
        removed += frequency
        if removed * 2 >= len(arr):
            return chosen
    return 0


class Solution:
    def minSetSize(self, arr: list[int]) -> int:
        return solve(arr)
