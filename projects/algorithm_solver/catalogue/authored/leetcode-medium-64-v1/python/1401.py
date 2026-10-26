"""1401. Circle and Rectangle Overlapping: compare the nearest rectangle point with the squared radius."""


def solve(radius: int, xCenter: int, yCenter: int, x1: int, y1: int, x2: int, y2: int) -> bool:
    """O(1) time and O(1) auxiliary space; inputs are read-only."""
    nearest_x = min(max(xCenter, x1), x2)
    nearest_y = min(max(yCenter, y1), y2)
    dx, dy = xCenter - nearest_x, yCenter - nearest_y
    return dx * dx + dy * dy <= radius * radius


class Solution:
    def checkOverlap(self, radius: int, xCenter: int, yCenter: int, x1: int, y1: int, x2: int, y2: int) -> bool:
        return solve(radius, xCenter, yCenter, x1, y1, x2, y2)
