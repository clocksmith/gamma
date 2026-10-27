"""469. Convex Polygon. Consistent nonzero cross-product signs for the supplied simple polygon."""

def solve(points: list[list[int]]) -> bool:
    sign = 0
    n = len(points)
    for i in range(n):
        a, b, c = points[i], points[(i + 1) % n], points[(i + 2) % n]
        cross = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
        if cross:
            current = 1 if cross > 0 else -1
            if sign and current != sign:
                return False
            sign = current
    return True


class Solution:
    def isConvex(self, points: list[list[int]]) -> bool:
        return solve(points)
