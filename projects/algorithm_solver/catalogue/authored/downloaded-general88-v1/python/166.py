"""166. Fraction to Recurring Decimal (Medium).

Specification: https://leetcode.com/problems/fraction-to-recurring-decimal/description/
"""


def solve(numerator: int, denominator: int) -> str:
    if numerator == 0:
        return '0'
    result = ''
    if (numerator < 0) != (denominator < 0):
        result += '-'
    num = abs(numerator)
    den = abs(denominator)
    result += str(num // den)
    remainder = num % den
    if remainder == 0:
        return result
    result += '.'
    seen = {}
    while remainder != 0:
        if remainder in seen:
            index = seen[remainder]
            return result[:index] + '(' + result[index:] + ')'
        seen[remainder] = len(result)
        remainder *= 10
        result += str(remainder // den)
        remainder %= den
    return result


class Solution:
    def fractionToDecimal(self, numerator: int, denominator: int) -> str:
        return solve(numerator, denominator)
