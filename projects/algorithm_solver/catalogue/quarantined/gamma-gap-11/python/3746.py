"""3746. Minimum String Length After Balanced Removals."""
from __future__ import annotations


def solve(s: str) -> int:
    """O(n) time and O(1) auxiliary space; balanced removals preserve the difference in letter counts."""
    balance = 0
    for char in s:
        balance += 1 if char == 'a' else -1
    return abs(balance)


class Solution:
    def minLengthAfterRemovals(self, s: str) -> int:
        return solve(s)
