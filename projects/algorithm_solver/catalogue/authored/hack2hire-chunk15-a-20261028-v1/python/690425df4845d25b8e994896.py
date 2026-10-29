"""Hack2Hire 690425df4845d25b8e994896 (Closest Pair of Points) over an INFERRED spec; qualification unknown."""

import math


def solve(points):
    pts = sorted((x, y) for x, y in points)
    best = [(pts[0][0] - pts[1][0]) ** 2 + (pts[0][1] - pts[1][1]) ** 2]

    def rec(lo, hi):
        if hi - lo <= 3:
            part = pts[lo:hi]
            for i in range(len(part)):
                for j in range(i + 1, len(part)):
                    d = (part[i][0] - part[j][0]) ** 2 + (part[i][1] - part[j][1]) ** 2
                    if d < best[0]:
                        best[0] = d
            return sorted(part, key=lambda q: q[1])
        mid = (lo + hi) // 2
        mid_x = pts[mid][0]
        left, right = rec(lo, mid), rec(mid, hi)
        merged, i, j = [], 0, 0
        while i < len(left) and j < len(right):
            if left[i][1] <= right[j][1]:
                merged.append(left[i])
                i += 1
            else:
                merged.append(right[j])
                j += 1
        merged.extend(left[i:])
        merged.extend(right[j:])
        strip = [q for q in merged if (q[0] - mid_x) ** 2 < best[0]]
        for i in range(len(strip)):
            for j in range(i + 1, len(strip)):
                dy = strip[j][1] - strip[i][1]
                if dy * dy >= best[0]:
                    break
                d = (strip[j][0] - strip[i][0]) ** 2 + dy * dy
                if d < best[0]:
                    best[0] = d
        return merged

    rec(0, len(pts))
    return math.sqrt(best[0])


class Solution:
    def closestPair(self, points):
        return solve(points)
