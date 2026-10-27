"""166. Fraction to Recurring Decimal."""
def solve(numerator: int, denominator: int) -> str:
    if numerator == 0:
        return '0'
    sign = '-' if (numerator < 0) ^ (denominator < 0) else ''
    numerator, denominator = abs(numerator), abs(denominator)
    integer, remainder = divmod(numerator, denominator)
    if remainder == 0:
        return sign + str(integer)
    digits = []
    positions = {}
    while remainder and remainder not in positions:
        positions[remainder] = len(digits)
        value, remainder = divmod(remainder * 10, denominator)
        digits.append(str(value))
    if remainder:
        index = positions[remainder]
        digits.insert(index, '(')
        digits.append(')')
    return sign + str(integer) + '.' + ''.join(digits)

class Solution:
    def fractionToDecimal(self, numerator: int, denominator: int) -> str:
        return solve(numerator, denominator)
