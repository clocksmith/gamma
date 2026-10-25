"""972. Equal Rational Numbers."""

def _fraction(text: str) -> tuple[int, int]:
    whole, separator, fraction = text.partition('.')
    if not separator:
        return int(whole), 1
    prefix, repeating_separator, repeat = fraction.partition('(')
    scale = 10 ** len(prefix)
    numerator = int(whole) * scale + int(prefix or '0')
    if not repeating_separator:
        return numerator, scale
    repeat = repeat[:-1]
    cycle = 10 ** len(repeat) - 1
    return numerator * cycle + int(repeat), scale * cycle


def solve(s: str, t: str) -> bool:
    """Parse exact fractions, including repeating nines; no floating-point comparison."""
    left_num, left_den = _fraction(s)
    right_num, right_den = _fraction(t)
    return left_num * right_den == right_num * left_den


class Solution:
    def isRationalEqual(self, s: str, t: str) -> bool:
        return solve(s, t)
