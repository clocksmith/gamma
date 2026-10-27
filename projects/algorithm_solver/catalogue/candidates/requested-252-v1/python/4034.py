"""4034. Minimum Bishop Moves to Reach Target
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/minimum-bishop-moves-to-reach-target/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4034.Minimum%20Bishop%20Moves%20to%20Reach%20Target/README_EN.md
Complexity: O(1) time and space.
Empty 8-by-8 board; one-indexed coordinates; inputs preserved.
"""

from __future__ import annotations

def solve(source, target):
    a, b = source
    c, d = target
    if a == c and b == d:
        return 0
    if (a + b - c - d) % 2:
        return -1
    return 1 if abs(a - c) == abs(b - d) else 2


class Solution:
    def minBishopMoves(self, source, target):
        return solve(source, target)
