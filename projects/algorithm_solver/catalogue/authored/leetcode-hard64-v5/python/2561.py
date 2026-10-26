"""2561. Rearranging Fruits. Pair opposite surplus values and allow swaps through the global minimum."""


def solve(basket1: list[int], basket2: list[int]) -> int:
    """O(n log n) time and O(n) space. Inputs are preserved."""
    difference = {}
    smallest = min(min(basket1), min(basket2))
    for value in basket1:
        difference[value] = difference.get(value, 0) + 1
    for value in basket2:
        difference[value] = difference.get(value, 0) - 1
    surplus = []
    for value, count in difference.items():
        if count % 2:
            return -1
        surplus.extend([value] * (abs(count) // 2))
    surplus.sort()
    return sum(min(surplus[index], 2 * smallest) for index in range(len(surplus) // 2))


class Solution:
    def minCost(self, basket1: list[int], basket2: list[int]) -> int:
        return solve(basket1, basket2)
