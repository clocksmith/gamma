"""2543. Check if Point Is Reachable. The reachable coordinates have a greatest common divisor that is a power of two."""

from math import gcd


def solve(targetX: int, targetY: int) -> bool:
    """O(log(min(targetX,targetY))) time and O(1) space. Inputs are preserved."""
    common = gcd(targetX, targetY)
    return common & (common - 1) == 0


class Solution:
    def isReachable(self, targetX: int, targetY: int) -> bool:
        return solve(targetX, targetY)
