"""Original frontend 3899 variant; qualification unknown."""

def solve(sides):
    from math import acos, degrees
    a, b, c = sorted(sides)
    if a + b <= c:
        return []
    return [degrees(acos(max(-1.0, min(1.0, (y * y + z * z - x * x) / (2 * y * z))))) for x, y, z in [(a, b, c), (b, a, c), (c, a, b)]]


class Solution:
    def internalAngles(self, sides):
        return solve(sides)
