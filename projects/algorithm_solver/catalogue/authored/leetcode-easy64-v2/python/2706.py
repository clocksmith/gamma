"""2706. Buy Two Chocolates (Easy).

Specification: https://leetcode.com/problems/buy-two-chocolates/description/
"""


def solve(prices: list[int], money: int) -> int:
    """O(n) time, O(1) space; find two distinct purchases without sorting prices."""
    first = second = float('inf')
    for price in prices:
        if price < first:
            second, first = first, price
        elif price < second:
            second = price
    cost = first + second
    return money - cost if cost <= money else money


class Solution:
    def buyChoco(self, prices: list[int], money: int) -> int:
        return solve(prices, money)
