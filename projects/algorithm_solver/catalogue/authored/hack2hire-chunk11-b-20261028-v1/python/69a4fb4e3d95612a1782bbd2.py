"""Hack2Hire 69a4fb4e3d95612a1782bbd2 (Largest Rectangle Area, variant 1 of 2) over an INFERRED spec; qualification unknown."""


def solve(points):
    ordered = sorted((p[0], p[1]) for p in points)
    first_column = {}  # (y1, y2) packed as y1 * 40001 + y2 -> smallest x holding both
    best = 0
    i = 0
    while i < len(ordered):
        x = ordered[i][0]
        j = i
        while j < len(ordered) and ordered[j][0] == x:
            j += 1
        ys = [p[1] for p in ordered[i:j]]
        for a in range(len(ys)):
            for b in range(a + 1, len(ys)):
                key = ys[a] * 40001 + ys[b]
                seen = first_column.get(key)
                if seen is None:
                    first_column[key] = x
                else:
                    area = (x - seen) * (ys[b] - ys[a])
                    if area > best:
                        best = area
        i = j
    return best


class Solution:
    def largestRectangleArea(self, points):
        return solve(points)
