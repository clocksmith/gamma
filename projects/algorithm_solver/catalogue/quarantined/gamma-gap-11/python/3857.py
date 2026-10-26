"""3857. Minimum Cost to Split into Ones."""
from __future__ import annotations


def solve(n: int) -> int:
    """O(1) time and space; every split removes exactly a*b unordered pairs, telescoping to n choose 2."""
    return n * (n - 1) // 2


class Solution:
    def minCost(self, n: int) -> int:
        return solve(n)
