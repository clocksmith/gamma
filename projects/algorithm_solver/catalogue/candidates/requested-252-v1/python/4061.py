"""4061. Minimum Queen Moves to Reach Target
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/minimum-queen-moves-to-reach-target/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4061.Minimum%20Queen%20Moves%20to%20Reach%20Target/README_EN.md
Complexity: O(1) time and space.
Empty 8-by-8 board with one-indexed coordinates. Inputs preserved.
"""

from __future__ import annotations

def solve(source, target):
    row, col = abs(source[0]-target[0]), abs(source[1]-target[1])
    if row == col == 0:
        return 0
    return 1 if row == 0 or col == 0 or row == col else 2


class Solution:
    def minQueenMoves(self, source, target):
        return solve(source, target)
