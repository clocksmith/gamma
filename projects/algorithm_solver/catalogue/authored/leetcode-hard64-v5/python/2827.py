"""2827. Number of Beautiful Integers in the Range. Digit DP over parity balance, divisibility, and leading zeros."""

from functools import lru_cache


def solve(low: int, high: int, k: int) -> int:
    """O(10*d^2*k) time and O(d^2*k) space for d decimal digits. Inputs are preserved."""
    def through(bound):
        if bound <= 0:
            return 0
        digits = [int(char) for char in str(bound)]

        @lru_cache(None)
        def visit(index, balance, remainder, tight, started):
            if index == len(digits):
                return int(started and balance == 0 and remainder == 0)
            if abs(balance) > len(digits) - index:
                return 0
            answer = 0
            upper = digits[index] if tight else 9
            for digit in range(upper + 1):
                next_tight = tight and digit == upper
                if not started and digit == 0:
                    answer += visit(index + 1, 0, 0, next_tight, False)
                else:
                    next_balance = balance + (1 if digit % 2 else -1)
                    answer += visit(index + 1, next_balance, (remainder * 10 + digit) % k, next_tight, True)
            return answer

        return visit(0, 0, 0, True, False)

    return through(high) - through(low - 1)


class Solution:
    def numberOfBeautifulIntegers(self, low: int, high: int, k: int) -> int:
        return solve(low, high, k)
