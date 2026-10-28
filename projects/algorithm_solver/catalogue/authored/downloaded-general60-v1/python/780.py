"""780. Reaching Points (Hard).

Specification: https://leetcode.com/problems/reaching-points/description/
"""


def solve(sx: int, sy: int, tx: int, ty: int) -> bool:
    x, y = tx, ty
    while x >= sx and y >= sy:
        if x == sx and y == sy:
            return True
        if x == y:
            return False
        if x > y:
            if y > sy:
                x %= y
            else:
                return (x - sx) % y == 0
        else:
            if x > sx:
                y %= x
            else:
                return (y - sy) % x == 0
    return False


class Solution:
    def reachingPoints(self, sx: int, sy: int, tx: int, ty: int) -> bool:
        return solve(sx, sy, tx, ty)
