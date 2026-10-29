"""Original frontend 1274 variant; qualification unknown."""


def _has_ships(sea, tr, bl) -> bool:
    if hasattr(sea, "hasShips"):
        return sea.hasShips(tr, bl)
    x2, y2 = tr
    x1, y1 = bl
    return any(x1 <= sx <= x2 and y1 <= sy <= y2 for sx, sy in sea)


def solve(sea, topRight, bottomLeft) -> int:
    def count_rec(tr, bl) -> int:
        x2, y2 = tr
        x1, y1 = bl
        if x1 > x2 or y1 > y2 or not _has_ships(sea, tr, bl):
            return 0
        if x1 == x2 and y1 == y2:
            return 1
        mx = (x1 + x2) // 2
        my = (y1 + y2) // 2
        return (
            count_rec([mx, my], [x1, y1])
            + count_rec([x2, my], [mx + 1, y1])
            + count_rec([mx, y2], [x1, my + 1])
            + count_rec([x2, y2], [mx + 1, my + 1])
        )
    return count_rec(topRight, bottomLeft)


countShips = solve


class Solution:
    def countShips(self, sea, topRight, bottomLeft) -> int:
        return solve(sea, topRight, bottomLeft)
