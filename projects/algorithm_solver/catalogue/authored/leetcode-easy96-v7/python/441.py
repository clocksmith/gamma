"""441. Arranging Coins (Easy).

Specification: https://leetcode.com/problems/arranging-coins/description/
"""


def solve(n: int) -> int:
    """O(log n) time, O(1) space; the 32-bit input bound permits an exact 65536-row upper bound."""
    low = 0
    high = min(n, 65536)
    while low < high:
        middle = low + (high - low + 1) // 2
        required = middle * (middle + 1) // 2
        if required <= n:
            low = middle
        else:
            high = middle - 1
    return low


class Solution:
    def arrangeCoins(self, n: int) -> int:
        return solve(n)
