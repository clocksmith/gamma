"""2849. Determine if a Cell Is Reachable at a Given Time: compare time with Chebyshev distance and handle the one-step return exception."""


def solve(sx: int, sy: int, fx: int, fy: int, t: int) -> bool:
    """O(1) time and O(1) auxiliary space; inputs are read-only."""
    distance = max(abs(sx - fx), abs(sy - fy))
    return t >= distance and not (distance == 0 and t == 1)


class Solution:
    def isReachableAtTime(self, sx: int, sy: int, fx: int, fy: int, t: int) -> bool:
        return solve(sx, sy, fx, fy, t)
