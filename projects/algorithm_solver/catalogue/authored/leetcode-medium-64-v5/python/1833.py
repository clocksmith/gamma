"""1833. Maximum Ice Cream Bars: count prices and buy affordable bars in ascending price order."""


def solve(costs: list[int], coins: int) -> int:
    """O(n + M) time and O(M) auxiliary space, with M the largest price; inputs are read-only."""
    largest = max(costs)
    counts = [0] * (largest + 1)
    for cost in costs:
        counts[cost] += 1
    remaining = coins
    bought = 0
    for price in range(1, largest + 1):
        if price > remaining:
            break
        quantity = min(counts[price], remaining // price)
        bought += quantity
        remaining -= quantity * price
    return bought


class Solution:
    def maxIceCream(self, costs: list[int], coins: int) -> int:
        return solve(costs, coins)
