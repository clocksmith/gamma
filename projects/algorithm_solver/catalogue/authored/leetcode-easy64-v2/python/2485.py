"""2485. Find the Pivot Integer (Easy).

Specification: https://leetcode.com/problems/find-the-pivot-integer/description/
"""

from math import isqrt


def solve(n: int) -> int:
    """O(1) time and space in the bounded domain; a pivot squares to n*(n+1)/2."""
    total = n * (n + 1) // 2
    pivot = isqrt(total)
    return pivot if pivot * pivot == total else -1


class Solution:
    def pivotInteger(self, n: int) -> int:
        return solve(n)
