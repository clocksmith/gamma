"""3602. Hexadecimal and Hexatrigesimal Conversion (Easy).

Specification: https://leetcode.com/problems/hexadecimal-and-hexatrigesimal-conversion/description/
"""


def solve(n: int) -> str:
    """O(log n) time and space; n <= 1000 keeps both powers exactly representable."""
    alphabet = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    def encode(value: int, base: int) -> str:
        digits = []
        while value > 0:
            digits.append(alphabet[value % base])
            value //= base
        return ''.join(reversed(digits))
    return encode(n * n, 16) + encode(n * n * n, 36)


class Solution:
    def concatHex36(self, n: int) -> str:
        return solve(n)
