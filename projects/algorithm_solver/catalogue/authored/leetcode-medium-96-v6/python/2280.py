"""2280. Minimum Lines to Represent a Line Chart: detect slope changes with exact cross products rather than floating division."""


def solve(stockPrices: list[list[int]]) -> int:
    """O(n log n) time and O(n) auxiliary space on the bounded coordinate domain; inputs are read-only."""
    if len(stockPrices) < 2:
        return 0
    points = sorted(stockPrices, key=lambda point: point[0])
    previous_dx = points[1][0] - points[0][0]
    previous_dy = points[1][1] - points[0][1]
    lines = 1
    for index in range(2, len(points)):
        dx = points[index][0] - points[index - 1][0]
        dy = points[index][1] - points[index - 1][1]
        if dy * previous_dx != previous_dy * dx:
            lines += 1
        previous_dx, previous_dy = dx, dy
    return lines


class Solution:
    def minimumLines(self, stockPrices: list[list[int]]) -> int:
        return solve(stockPrices)
