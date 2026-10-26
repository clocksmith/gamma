"""2861. Maximum Number of Alloys: binary search each machine using its exact metal shortfall cost."""


def solve(n: int, k: int, budget: int, composition: list[list[int]], stock: list[int], cost: list[int]) -> int:
    """O(k * n * log(U + 1)) time and O(1) auxiliary space, where U is the per-machine production bound; inputs are read-only."""
    best = 0
    for machine in range(k):
        recipe = composition[machine]
        upper = min((stock[index] + budget // cost[index]) // recipe[index] for index in range(n))
        low, high = 0, upper
        while low < high:
            amount = (low + high + 1) // 2
            spending = 0
            for index in range(n):
                spending += max(0, amount * recipe[index] - stock[index]) * cost[index]
                if spending > budget:
                    break
            if spending <= budget:
                low = amount
            else:
                high = amount - 1
        best = max(best, low)
    return best


class Solution:
    def maxNumberOfAlloys(self, n: int, k: int, budget: int, composition: list[list[int]], stock: list[int], cost: list[int]) -> int:
        return solve(n, k, budget, composition, stock, cost)
