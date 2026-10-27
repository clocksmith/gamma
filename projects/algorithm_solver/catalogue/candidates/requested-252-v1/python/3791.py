"""3791. Number of Balanced Integers in a Range
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/number-of-balanced-integers-in-a-range/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3700-3799/3791.Number%20of%20Balanced%20Integers%20in%20a%20Range/README_EN.md
Complexity: O(D^2*100) time; O(D^2*10) memo space.
Leading zero padding can only negate the parity difference; equality is invariant. Excludes zero; no positive one-digit number qualifies.
"""

from __future__ import annotations
from functools import cache

def solve(low, high):
    def cumulative(bound):
        if bound < 1:
            return 0
        digits = tuple(map(int, str(bound)))
        @cache
        def count(position, difference, tight):
            if position == len(digits):
                return int(difference == 0)
            limit = digits[position] if tight else 9
            sign = 1 if position % 2 == 0 else -1
            return sum(count(position + 1, difference + sign * digit, tight and digit == limit) for digit in range(limit + 1))
        return count(0, 0, True) - 1
    return cumulative(high) - cumulative(low - 1)


class Solution:
    def countBalanced(self, low, high):
        return solve(low, high)
