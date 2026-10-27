"""3959. Check Good Integer.

Specification: https://leetcode.com/problems/check-good-integer/description/
"""

from __future__ import annotations


def solve(n: int) -> bool:
    """O(log n) time and O(1) space. Inputs are preserved."""
    difference = 0
    while n:
        n, digit = divmod(n, 10)
        difference += digit * (digit - 1)
    return difference >= 50
