"""3001. Minimum Moves to Capture The Queen: check unobstructed rook and bishop attacks before using the two-move bound."""


def solve(a: int, b: int, c: int, d: int, e: int, f: int) -> int:
    """O(1) time and O(1) auxiliary space; inputs are read-only."""
    if a == e and not (c == a and min(b, f) < d < max(b, f)):
        return 1
    if b == f and not (d == b and min(a, e) < c < max(a, e)):
        return 1
    if abs(c - e) == abs(d - f):
        blocked = (abs(a - c) == abs(b - d)
                   and min(c, e) < a < max(c, e)
                   and min(d, f) < b < max(d, f))
        if not blocked:
            return 1
    return 2


class Solution:
    def minMovesToCaptureTheQueen(self, a: int, b: int, c: int, d: int, e: int, f: int) -> int:
        return solve(a, b, c, d, e, f)
