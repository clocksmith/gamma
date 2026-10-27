"""3946. Maximum Number of Items From Sale I.

Specification: https://leetcode.com/problems/maximum-number-of-items-from-sale-i/description/
"""

from __future__ import annotations


def solve(items: list[list[int]], budget: int) -> int:
    """O(n^2 + n * budget) time and O(budget) space. Inputs are preserved."""
    best = [0] * (budget + 1)
    for index, (factor, price) in enumerate(items):
        bonus = sum(other != index and values[0] % factor == 0 for other, values in enumerate(items))
        # Activate this type once, then add extra copies without repeating its bonus.
        for money in range(budget, price - 1, -1):
            best[money] = max(best[money], best[money - price] + 1 + bonus)
        for money in range(price, budget + 1):
            best[money] = max(best[money], best[money - price] + 1)
    return best[budget]

# Native judge method name is not established; canonical solve is the supported entry point.
