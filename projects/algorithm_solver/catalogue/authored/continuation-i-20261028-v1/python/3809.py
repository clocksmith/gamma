def solve(towers, center, radius):
    best = None
    for x, y, quality in towers:
        if abs(x - center[0]) + abs(y - center[1]) <= radius:
            key = (-quality, x, y)
            if best is None or key < best:
                best = key
    return [-1, -1] if best is None else [best[1], best[2]]


class Solution:
    def bestTower(self, towers, center, radius):
        return solve(towers, center, radius)
