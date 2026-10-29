"""Original frontend 356 variant; qualification unknown."""


def solve(points) -> bool:
    pts = {(x, y) for x, y in points}
    xs = [x for x, _ in pts]
    sum_x = min(xs) + max(xs)
    return all((sum_x - x, y) in pts for x, y in pts)


isReflected = solve


class Solution:
    def isReflected(self, points) -> bool:
        return solve(points)
