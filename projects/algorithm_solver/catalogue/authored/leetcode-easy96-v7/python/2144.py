"""2144. Minimum Cost of Buying Candies With Discount (Easy).

Specification: https://leetcode.com/problems/minimum-cost-of-buying-candies-with-discount/description/
"""


def solve(cost: list[int]) -> int:
    """O(n log n) time, O(n) space; make every third candy free in descending-price order; preserve cost."""
    prices = sorted(cost, reverse=True)
    return sum(price for index, price in enumerate(prices) if index % 3 != 2)


class Solution:
    def minimumCost(self, cost: list[int]) -> int:
        return solve(cost)
