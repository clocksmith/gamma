"""Hack2Hire 678884a8402dc47b67a1494c (Integer to English Converter, level 2) over an INFERRED spec; qualification unknown."""

ONES = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten', 'Eleven', 'Twelve', 'Thirteen',
        'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen']
TENS = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']


def _below_thousand(x):
    words = []
    if x >= 100:
        words += [ONES[x // 100], 'Hundred']
        x %= 100
    if x >= 20:
        words.append(TENS[x // 10])
        x %= 10
    if x:
        words.append(ONES[x])
    return words


def solve(num):
    return 'Zero' if num == 0 else ' '.join(_below_thousand(num))


class Solution:
    def numberToWords(self, num):
        return solve(num)
