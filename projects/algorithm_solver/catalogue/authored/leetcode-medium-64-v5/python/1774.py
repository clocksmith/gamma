"""1774. Closest Dessert Cost: enumerate distinct topping totals and compare every base with explicit lower-cost tie breaking."""


def solve(baseCosts: list[int], toppingCosts: list[int], target: int) -> int:
    """O((b + 1) * 3^t) expected time and O(3^t) space, with b bases and t toppings; inputs are read-only."""
    totals = {0}
    for cost in toppingCosts:
        totals = {total + count * cost for total in totals for count in (0, 1, 2)}
    best = baseCosts[0]
    for base in baseCosts:
        for topping in totals:
            candidate = base + topping
            difference = abs(candidate - target)
            if difference < abs(best - target) or (difference == abs(best - target) and candidate < best):
                best = candidate
    return best


class Solution:
    def closestCost(self, baseCosts: list[int], toppingCosts: list[int], target: int) -> int:
        return solve(baseCosts, toppingCosts, target)
