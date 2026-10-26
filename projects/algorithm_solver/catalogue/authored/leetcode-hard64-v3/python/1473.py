"""1473. Paint House III: neighborhood DP with two minima per prior layer; O(m*n*target) time and O(n*target) space."""


def solve(houses: list[int], cost: list[list[int]], m: int, n: int, target: int) -> int:
    infinity = float('inf')
    previous = [[infinity] * (n + 1) for _ in range(target + 1)]
    previous[0][0] = 0
    for index, painted in enumerate(houses):
        current = [[infinity] * (n + 1) for _ in range(target + 1)]
        for groups in range(1, min(target, index + 1) + 1):
            first = second = infinity
            first_color = -1
            for color, value in enumerate(previous[groups - 1]):
                if value < first:
                    second, first = first, value
                    first_color = color
                elif value < second:
                    second = value
            colors = (painted,) if painted else range(1, n + 1)
            for color in colors:
                different = second if color == first_color else first
                price = 0 if painted else cost[index][color - 1]
                current[groups][color] = min(previous[groups][color], different) + price
        previous = current
    answer = min(previous[target])
    return -1 if answer == infinity else answer


class Solution:
    def minCost(self, houses: list[int], cost: list[list[int]], m: int, n: int, target: int) -> int:
        return solve(houses, cost, m, n, target)
