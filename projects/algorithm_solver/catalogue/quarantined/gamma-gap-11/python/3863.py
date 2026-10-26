"""3863. Minimum Operations to Sort a String."""
from __future__ import annotations


def solve(s: str) -> int:
    """O(n) time and O(1) alphabet space; endpoint placement of global extrema determines the required proper-substring sorts."""
    if all(s[index - 1] <= s[index] for index in range(1, len(s))):
        return 0
    if len(s) == 2:
        return -1
    smallest = min(s)
    largest = max(s)
    if s[0] == smallest or s[-1] == largest:
        return 1
    if s[0] == largest and s[-1] == smallest and s.count(largest) == 1 and s.count(smallest) == 1:
        return 3
    return 2


class Solution:
    def minOperations(self, s: str) -> int:
        return solve(s)
