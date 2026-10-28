"""7. Reverse Integer (Easy).

Specification: https://leetcode.com/problems/reverse-integer/description/
"""


def solve(x: int) -> int:
    result = 0
    value = x
    while value != 0:
        digit = value % 10 if value > 0 else -((-value) % 10)
        result = result * 10 + digit
        value = int(value / 10) if value > 0 else -int((-value) / 10)
    if result > 2147483647 or result < -2147483648:
        return 0
    return result


class Solution:
    def reverse(self, x: int) -> int:
        return solve(x)
