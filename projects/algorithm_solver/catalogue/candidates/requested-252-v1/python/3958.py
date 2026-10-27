"""3958. Minimum Cost to Split into Ones II.

Specification: https://leetcode.com/problems/minimum-cost-to-split-into-ones-ii/description/
"""

from __future__ import annotations


def solve(n: int) -> int:
    """O(1) time and space; each unordered pair of final ones is separated exactly once. Input is preserved. Under n <= 50000000 the JavaScript integer product is exact."""
    return n * (n - 1) // 2


class Solution:
    def minCost(self, n: int) -> int:
        return solve(n)
