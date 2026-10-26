"""2335. Minimum Amount of Time to Fill Cups (Easy).

Specification: https://leetcode.com/problems/minimum-amount-of-time-to-fill-cups/description/
"""


def solve(amount: list[int]) -> int:
    """O(1) time and space for three amounts; maximum demand and half the total are tight bounds."""
    total = amount[0] + amount[1] + amount[2]
    largest = max(amount)
    return max(largest, (total + 1) // 2)


class Solution:
    def fillCups(self, amount: list[int]) -> int:
        return solve(amount)
