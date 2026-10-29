"""Hack2Hire 6788830e402dc47b67a1494a (Integer to English Converter, level 1) over an INFERRED spec; qualification unknown."""

DIGITS = ['Zero', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine']


def solve(num):
    return DIGITS[num]


class Solution:
    def numberToWords(self, num):
        return solve(num)
