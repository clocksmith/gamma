"""Original frontend 3279 variant; qualification unknown."""


def solve(height: int, positions, directions) -> int:
    period = 2 * height
    delta = [0] * (period + 2)
    cur = sum(positions)
    slope = 0
    for p, d in zip(positions, directions):
        if p == 0:
            d = "U"
        elif p == height:
            d = "D"
        if d == "U":
            slope += 1
            t1 = height - p
            t2 = t1 + height
            delta[t1] -= 2
            delta[t2] += 2
        else:
            slope -= 1
            t1 = p
            t2 = t1 + height
            delta[t1] += 2
            delta[t2] -= 2
    best = cur
    for t in range(1, period + 1):
        cur += slope
        if cur > best:
            best = cur
        slope += delta[t]
    return best


maxArea = solve


class Solution:
    def maxArea(self, height: int, positions, directions) -> int:
        return solve(height, positions, directions)
