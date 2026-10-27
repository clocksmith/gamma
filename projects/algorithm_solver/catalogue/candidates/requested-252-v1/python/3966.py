"""3966. Count Good Integers in a Range
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/count-good-integers-in-a-range/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3966.Count%20Good%20Integers%20in%20a%20Range/README_EN.md
Complexity: O(log r * 100) time, O(log r * 10) space.
Leading padding zeros do not constrain the first real digit; zero cancels in the range difference. r <= 1e15, counts exactly representable. Inputs preserved; native method pending.
"""

from __future__ import annotations
from functools import lru_cache

def solve(l, r, k):
    def count(bound):
        if bound < 0:
            return 0
        digits = list(map(int, str(bound)))
        @lru_cache(None)
        def visit(position, previous, tight):
            if position == len(digits):
                return 1
            limit = digits[position] if tight else 9
            total = 0
            for digit in range(limit + 1):
                if previous == 10 and digit == 0:
                    following = 10
                elif previous == 10 or abs(previous - digit) <= k:
                    following = digit
                else:
                    continue
                total += visit(position + 1, following, tight and digit == limit)
            return total
        return visit(0, 10, True)
    return count(r) - count(l - 1)
