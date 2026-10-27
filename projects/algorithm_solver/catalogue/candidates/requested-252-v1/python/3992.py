"""3992. Rearrange String to Avoid Character Pair
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/rearrange-string-to-avoid-character-pair/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3992.Rearrange%20String%20to%20Avoid%20Character%20Pair/README_EN.md
Complexity: O(n) time and output space.
All y precede all x. Any valid permutation is accepted; unrelated letters retain relative order.
"""

from __future__ import annotations

def solve(s, x, y):
    return y * s.count(y) + ''.join(ch for ch in s if ch != y)


class Solution:
    def rearrangeString(self, s, x, y):
        return solve(s, x, y)
