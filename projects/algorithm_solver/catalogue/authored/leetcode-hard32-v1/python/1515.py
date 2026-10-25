"""1515. Best Position for a Service Centre."""

from math import hypot


def solve(positions: list[list[int]]) -> float:
    """Nested convex ternary search: O(n*I^2) time, O(1) workspace, I=80."""
    min_x = min(point[0] for point in positions)
    max_x = max(point[0] for point in positions)
    min_y = min(point[1] for point in positions)
    max_y = max(point[1] for point in positions)

    def distance(x: float, y: float) -> float:
        return sum(hypot(x - px, y - py) for px, py in positions)

    def best_at_x(x: float) -> float:
        low, high = min_y, max_y
        for _ in range(80):
            left = low + (high - low) / 3
            right = high - (high - low) / 3
            if distance(x, left) <= distance(x, right):
                high = right
            else:
                low = left
        return distance(x, (low + high) / 2)

    # A minimizer lies in the bounding box; minimizing over y preserves convexity.
    low, high = min_x, max_x
    for _ in range(80):
        left = low + (high - low) / 3
        right = high - (high - low) / 3
        if best_at_x(left) <= best_at_x(right):
            high = right
        else:
            low = left
    return best_at_x((low + high) / 2)


class Solution:
    def getMinDistSum(self, positions: list[list[int]]) -> float:
        return solve(positions)
