"""2742. Painting the Walls. Zero-one knapsack on the number of walls covered by a paid job."""


def solve(cost: list[int], time: list[int]) -> int:
    """O(n^2) time and O(n) space. Inputs are preserved."""
    size = len(cost)
    best = [0] + [float("inf")] * size
    for amount, duration in zip(cost, time):
        for covered in range(size - 1, -1, -1):
            following = min(size, covered + duration + 1)
            best[following] = min(best[following], best[covered] + amount)
    return best[size]


class Solution:
    def paintWalls(self, cost: list[int], time: list[int]) -> int:
        return solve(cost, time)
