"""356. Line Reflection."""
def solve(points: list[list[int]]) -> bool:
    values = {(x, y) for x, y in points}
    minimum = min(x for x, _ in points)
    maximum = max(x for x, _ in points)
    total = minimum + maximum
    return all((total - x, y) in values for x, y in points)

class Solution:
    def isReflected(self, points: list[list[int]]) -> bool:
        return solve(points)
