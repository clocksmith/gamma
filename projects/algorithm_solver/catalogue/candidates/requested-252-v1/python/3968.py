"""3968. Maximum Manhattan Distance After All Moves
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/maximum-manhattan-distance-after-all-moves/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3968.Maximum%20Manhattan%20Distance%20After%20All%20Moves/README_EN.md
Complexity: O(n) time, O(1) auxiliary space.
Maximum final distance, not maximum intermediate distance. Each underscore is independently chosen; input preserved.
"""

from __future__ import annotations

def solve(moves):
    return abs(moves.count('U') - moves.count('D')) + abs(moves.count('R') - moves.count('L')) + moves.count('_')


class Solution:
    def maxDistance(self, moves):
        return solve(moves)
