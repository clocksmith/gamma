"""4060. Count Evenly Good Integers
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/count-evenly-good-integers/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4060.Count%20Evenly%20Good%20Integers/README_EN.md
Complexity: O(10 log r) time, O(log r) states.
Leading padding zeros are not digits of a positive integer. Internal zero digits count as even; integers with zero even digits qualify. All counts fit exact JS Number range.
"""

from __future__ import annotations
from functools import cache

def solve(l, r):
    def count(bound):
        if bound < 1:
            return 0
        digits = tuple(map(int, str(bound)))
        @cache
        def visit(position, parity, started, tight):
            if position == len(digits):
                return int(started and parity == 0)
            limit = digits[position] if tight else 9
            answer = 0
            for digit in range(limit+1):
                following = started or digit != 0
                next_parity = parity ^ int(following and digit % 2 == 0)
                answer += visit(position+1, next_parity, following, tight and digit == limit)
            return answer
        return visit(0, 0, False, True)
    return count(r)-count(l-1)


class Solution:
    def countEvenlyGoodIntegers(self, l, r):
        return solve(l, r)
