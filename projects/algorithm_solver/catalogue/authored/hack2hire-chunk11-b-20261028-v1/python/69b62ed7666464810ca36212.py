"""Hack2Hire 69b62ed7666464810ca36212 (Largest Rectangle Area, variant 2 of 2) over an INFERRED spec; qualification unknown."""


def solve(points):
    groups = {}  # (x sum, y sum, squared length) -> point index pairs: diagonals sharing midpoint and length
    n = len(points)
    for i in range(n):
        px, py = points[i]
        for j in range(i + 1, n):
            qx, qy = points[j]
            dx, dy = qx - px, qy - py
            groups.setdefault((px + qx, py + qy, dx * dx + dy * dy), []).append((i, j))
    best = 0
    for pairs in groups.values():
        for a in range(len(pairs)):
            p = points[pairs[a][0]]
            for b in range(a + 1, len(pairs)):
                u, v = points[pairs[b][0]], points[pairs[b][1]]
                area = abs((u[0] - p[0]) * (v[1] - p[1]) - (u[1] - p[1]) * (v[0] - p[0]))
                if area > best:
                    best = area
    return best


class Solution:
    def largestRectangleArea(self, points):
        return solve(points)
