"""7. Reverse Integer (Easy).

Specification: https://leetcode.com/problems/reverse-integer/description/
"""


def solve(x: int) -> int:
    value = x if x < 0 else -x
    result = 0
    last_digit = -8 if x < 0 else -7
    while value:
        quotient, digit = divmod(value, 10)
        if digit:
            quotient += 1
            digit -= 10
        if result < -214748364 or (result == -214748364 and digit < last_digit):
            return 0
        result = result * 10 + digit
        value = quotient
    return result if x < 0 else -result


class Solution:
    def reverse(self, x: int) -> int:
        return solve(x)
