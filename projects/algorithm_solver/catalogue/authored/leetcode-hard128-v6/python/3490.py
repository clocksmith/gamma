"""3490. Count Beautiful Numbers.

Digit dynamic programming memoizes digit sum and exact product, distinguishing leading zeros from zero digits; O(10*S) time and O(S) space for reached states. Inputs are preserved.
"""

from functools import cache


def solve(l: int, r: int) -> int:
    def count_through(bound):
        if bound <= 0:
            return 0
        digits = tuple(map(int, str(bound)))

        @cache
        def visit(position, total, product, tight):
            if position == len(digits):
                return int(total > 0 and product % total == 0)
            limit = digits[position] if tight else 9
            answer = 0
            for digit in range(limit + 1):
                following = 1 if total == 0 and digit == 0 else product * digit
                answer += visit(position + 1, total + digit, following, tight and digit == limit)
            return answer

        return visit(0, 0, 1, True)

    return count_through(r) - count_through(l - 1)


class Solution:
    def beautifulNumbers(self, l: int, r: int) -> int:
        return solve(l, r)
