"""393. UTF-8 Validation (Medium).

Specification: https://leetcode.com/problems/utf-8-validation/description/
"""


def solve(data: list[int]) -> bool:
    remaining = 0
    for byte in data:
        if remaining == 0:
            if byte >> 5 == 0b110:
                remaining = 1
            elif byte >> 4 == 0b1110:
                remaining = 2
            elif byte >> 3 == 0b11110:
                remaining = 3
            elif byte >> 7 != 0:
                return False
        else:
            if byte >> 6 != 0b10:
                return False
            remaining -= 1
    return remaining == 0


class Solution:
    def validUtf8(self, data: list[int]) -> bool:
        return solve(data)
