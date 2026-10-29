"""Hack2Hire 67888746402dc47b67a1494d (Integer to English Converter, level 3) over an INFERRED spec; qualification unknown."""

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

SCALES = ['', 'Thousand', 'Million', 'Billion']


def solve(num):
    if num == 0:
        return 'Zero'
    groups, scale = [], 0
    while num:
        chunk = num % 1000
        if chunk:
            groups.append(_below_thousand(chunk) + ([SCALES[scale]] if scale else []))
        num //= 1000
        scale += 1
    return ' '.join(word for group in reversed(groups) for word in group)


class Solution:
    def numberToWords(self, num):
        return solve(num)
