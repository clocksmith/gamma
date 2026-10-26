"""405. Convert a Number to Hexadecimal (Easy).

Specification: https://leetcode.com/problems/convert-a-number-to-hexadecimal/description/
"""


def solve(num: int) -> str:
    """O(1) bounded 32-bit conversion; use lowercase hexadecimal and two's complement."""
    value = num & 0xffffffff
    if value == 0:
        return '0'
    digits = '0123456789abcdef'
    result = []
    while value > 0:
        result.append(digits[value % 16])
        value //= 16
    return ''.join(reversed(result))


class Solution:
    def toHex(self, num: int) -> str:
        return solve(num)
