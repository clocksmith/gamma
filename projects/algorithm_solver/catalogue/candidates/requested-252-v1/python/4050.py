"""4050. Minimum Days to Score Exactly N Points
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/minimum-days-to-score-exactly-n-points/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4050.Minimum%20Days%20to%20Score%20Exactly%20N%20Points/README_EN.md
Complexity: O(n sqrt(n)) time, O(n) space.
Unbounded triangular-score knapsack. Charge one skip after every streak, then remove the final skip. No global precomputation or dependencies.
"""

from __future__ import annotations

def solve(n):
    best = [2*n+1] * (n+1)
    best[0] = 0
    length = 1
    while length*(length+1)//2 <= n:
        score = length*(length+1)//2
        cost = length+1
        for total in range(score, n+1):
            candidate = best[total-score]+cost
            if candidate < best[total]:
                best[total] = candidate
        length += 1
    return best[n]-1


class Solution:
    def minDays(self, n):
        return solve(n)
