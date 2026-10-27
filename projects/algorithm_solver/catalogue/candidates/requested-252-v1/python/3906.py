"""3906. Count Good Integers on a Grid Path
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/count-good-integers-on-a-grid-path/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3906.Count%20Good%20Integers%20on%20a%20Grid%20Path/README_EN.md
Complexity: O(16*10^2) time, O(16*10) states.
1<=l<=r<=9e15, exactly three D and R. Bound and answer fit JS safe integers; intermediate counts use BigInt.
"""

from __future__ import annotations
from functools import lru_cache

def solve(l, r, directions):
    selected = {0}
    position = 0
    for direction in directions:
        position += 4 if direction == 'D' else 1
        selected.add(position)
    def count(bound):
        if bound < 0:
            return 0
        digits = [int(character) for character in str(bound).zfill(16)]
        @lru_cache(None)
        def visit(index, previous, tight):
            if index == 16:
                return 1
            maximum = digits[index] if tight else 9
            minimum = previous if index in selected else 0
            answer = 0
            for digit in range(minimum, maximum + 1):
                answer += visit(index + 1, digit if index in selected else previous, tight and digit == maximum)
            return answer
        return visit(0, 0, True)
    return count(r) - count(l - 1)


class Solution:
    def countGoodIntegersOnPath(self, l, r, directions):
        return solve(l, r, directions)
