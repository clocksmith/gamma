"""3753. Total Waviness of Numbers in Range II
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/total-waviness-of-numbers-in-range-ii/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3700-3799/3753.Total%20Waviness%20of%20Numbers%20in%20Range%20II/README_EN.md
Complexity: O(D*10^3) time and O(D*10^2) memo space, D decimal digits.
JavaScript returns BigInt; Python returns int. Use an explicitly approved decimal-string transport, not Number coercion.
"""

from __future__ import annotations
from functools import cache

def solve(num1, num2):
    def cumulative(bound):
        if bound < 1:
            return 0
        digits = tuple(map(int, str(bound)))
        @cache
        def visit(position, older, previous, tight):
            if position == len(digits):
                return 1, 0
            count = total = 0
            limit = digits[position] if tight else 9
            for digit in range(limit + 1):
                next_tight = tight and digit == limit
                if previous == -1 and digit == 0:
                    ways, score = visit(position + 1, -1, -1, next_tight)
                    added = 0
                else:
                    ways, score = visit(position + 1, previous, digit, next_tight)
                    added = int(older != -1 and ((previous > older and previous > digit) or (previous < older and previous < digit)))
                count += ways
                total += score + added * ways
            return count, total
        return visit(0, -1, -1, True)[1]
    return cumulative(num2) - cumulative(num1 - 1)


class Solution:
    def totalWaviness(self, num1, num2):
        return solve(num1, num2)
