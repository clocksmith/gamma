"""Hack2Hire 6a95ede5cddc54478ddf6b5b (Triangle Point Membership) over an INFERRED spec; qualification unknown."""

def _cross(ox, oy, ax, ay, bx, by):
    return (ax - ox) * (by - oy) - (ay - oy) * (bx - ox)


def solve(x1, y1, x2, y2, x3, y3, xp, yp, xq, yq):
    if _cross(x1, y1, x2, y2, x3, y3) == 0:
        return 0

    def inside(px, py):
        d1 = _cross(x1, y1, x2, y2, px, py)
        d2 = _cross(x2, y2, x3, y3, px, py)
        d3 = _cross(x3, y3, x1, y1, px, py)
        negative = d1 < 0 or d2 < 0 or d3 < 0
        positive = d1 > 0 or d2 > 0 or d3 > 0
        return not (negative and positive)

    p, q = inside(xp, yp), inside(xq, yq)
    if p and q:
        return 3
    if p:
        return 1
    if q:
        return 2
    return 4


class Solution:
    def pointsBelong(self, x1, y1, x2, y2, x3, y3, xp, yp, xq, yq):
        return solve(x1, y1, x2, y2, x3, y3, xp, yp, xq, yq)
