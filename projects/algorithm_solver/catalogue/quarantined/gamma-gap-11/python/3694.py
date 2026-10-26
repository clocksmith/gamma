"""3694. Distinct Points Reachable After Substring Removal."""
from __future__ import annotations


def solve(s: str, k: int) -> int:
    """O(n) time and O(n) space; unique removed displacements correspond bijectively to final positions."""
    direction = {'U': (0, 1), 'D': (0, -1), 'L': (-1, 0), 'R': (1, 0)}
    horizontal = vertical = 0
    for index in range(k):
        dx, dy = direction[s[index]]
        horizontal += dx
        vertical += dy
    seen = {(horizontal, vertical)}
    for index in range(k, len(s)):
        dx, dy = direction[s[index - k]]
        horizontal -= dx
        vertical -= dy
        dx, dy = direction[s[index]]
        horizontal += dx
        vertical += dy
        seen.add((horizontal, vertical))
    return len(seen)


class Solution:
    def distinctPoints(self, s: str, k: int) -> int:
        return solve(s, k)
