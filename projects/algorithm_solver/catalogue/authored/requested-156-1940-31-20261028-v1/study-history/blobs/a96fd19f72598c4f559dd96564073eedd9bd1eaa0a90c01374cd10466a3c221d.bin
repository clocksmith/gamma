"""Original frontend 1924 variant; qualification unknown."""

import math


def solve(trees):
    pts = [tuple(p) for p in dict.fromkeys(tuple(t) for t in trees)]

    def dist(a, b):
        return math.hypot(a[0] - b[0], a[1] - b[1])

    def circle2(a, b):
        return ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0, dist(a, b) / 2.0)

    def circle3(a, b, c):
        ax, ay = a
        bx, by = b
        cx, cy = c
        d = 2.0 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
        if abs(d) < 1e-12:
            pairs = [circle2(a, b), circle2(b, c), circle2(a, c)]
            return max(pairs, key=lambda item: item[2])
        a2 = ax * ax + ay * ay
        b2 = bx * bx + by * by
        c2 = cx * cx + cy * cy
        ux = (a2 * (by - cy) + b2 * (cy - ay) + c2 * (ay - by)) / d
        uy = (a2 * (cx - bx) + b2 * (ax - cx) + c2 * (bx - ax)) / d
        return (ux, uy, math.hypot(ux - ax, uy - ay))

    c = (pts[0][0], pts[0][1], 0.0)
    for i in range(len(pts)):
        if dist((c[0], c[1]), pts[i]) > c[2] + 1e-9:
            c = (pts[i][0], pts[i][1], 0.0)
            for j in range(i):
                if dist((c[0], c[1]), pts[j]) > c[2] + 1e-9:
                    c = circle2(pts[i], pts[j])
                    for k in range(j):
                        if dist((c[0], c[1]), pts[k]) > c[2] + 1e-9:
                            c = circle3(pts[i], pts[j], pts[k])
    return [round(c[0], 5), round(c[1], 5), round(c[2], 5)]


outerTrees = solve


class Solution:
    def outerTrees(self, trees):
        return solve(trees)
