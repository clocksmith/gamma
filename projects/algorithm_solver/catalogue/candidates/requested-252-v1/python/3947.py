"""3947. Maximum Number of Items From Sale II.

Specification: https://leetcode.com/problems/maximum-number-of-items-from-sale-ii/description/
"""

from __future__ import annotations


def solve(items: list[list[int]], budget: int) -> int:
    """O(n log n) time and O(n) space; buy cheapest bounded two-copy offers, then cheapest plain copies. Inputs are preserved."""
    size = len(items)
    frequency = [0] * (size + 1)
    cheapest = min(price for _, price in items)
    for factor, _ in items:
        frequency[factor] += 1
    targets = [0] * (size + 1)
    for factor in range(1, size + 1):
        targets[factor] = sum(frequency[multiple] for multiple in range(factor, size + 1, factor))
    offers = sorted((price, targets[factor] - 1) for factor, price in items)
    money, answer = budget, 0
    for price, available in offers:
        if price >= 2 * cheapest:
            break
        copies = min(available, money // price)
        answer += 2 * copies
        money -= copies * price
        if copies < available:
            break
    return answer + money // cheapest
