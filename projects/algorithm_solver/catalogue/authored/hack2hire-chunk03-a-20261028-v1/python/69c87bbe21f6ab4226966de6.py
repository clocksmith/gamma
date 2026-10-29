"""Hack2Hire 69c87bbe21f6ab4226966de6 (Implement itoa()) over an INFERRED spec; qualification unknown."""


def solve(value):
    if value == 0:
        return '0'
    negative = value < 0
    magnitude = -value if negative else value
    digits = []
    while magnitude:
        magnitude, digit = divmod(magnitude, 10)
        digits.append(chr(48 + digit))
    if negative:
        digits.append('-')
    return ''.join(reversed(digits))


class Solution:
    def itoa(self, value):
        return solve(value)
