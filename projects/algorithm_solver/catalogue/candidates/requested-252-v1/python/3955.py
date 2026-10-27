"""3955. Valid Binary Strings With Cost Limit
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/valid-binary-strings-with-cost-limit/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3955.Valid%20Binary%20Strings%20With%20Cost%20Limit/README_EN.md
Complexity: O(n*2^n) worst-case output time and space, recursion depth n <= 12.
Outputs lexicographic order, which is an allowed deterministic order. Inputs preserved.
"""

from __future__ import annotations

def solve(n, k):
    answer = []
    def visit(prefix, cost):
        position = len(prefix)
        if position == n:
            answer.append(prefix)
            return
        visit(prefix + '0', cost)
        if (not prefix or prefix[-1] == '0') and cost + position <= k:
            visit(prefix + '1', cost + position)
    visit('', 0)
    return answer


class Solution:
    def generateValidStrings(self, n, k):
        return solve(n, k)
