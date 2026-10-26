"""3782. Last Remaining Integer After Alternating Deletion Operations."""
from __future__ import annotations


def solve(n: int) -> int:
    """O(log n) time and O(1) space; each pass retains the first number encountered and deletes the second."""
    first = step = 1
    remaining = n
    from_left = True
    while remaining > 1:
        if not from_left and remaining % 2 == 0:
            first += step
        remaining = (remaining + 1) // 2
        step *= 2
        from_left = not from_left
    return first


class Solution:
    def lastInteger(self, n: int) -> int:
        return solve(n)
