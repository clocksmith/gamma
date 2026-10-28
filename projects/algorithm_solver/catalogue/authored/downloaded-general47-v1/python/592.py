"""592. Fraction Addition and Subtraction (Medium).

Specification: https://leetcode.com/problems/fraction-addition-and-subtraction/description/
"""


import math
import re


def solve(expression: str) -> str:
    numerator = 0
    denominator = 1
    tokens = re.findall(r'[+-]?\d+/\d+', expression)
    for token in tokens:
        num_text, den_text = token.split('/')
        num = int(num_text)
        den = int(den_text)
        numerator = numerator * den + num * denominator
        denominator = denominator * den
        divisor = math.gcd(numerator, denominator)
        numerator //= divisor
        denominator //= divisor
    if denominator < 0:
        numerator = -numerator
        denominator = -denominator
    return f"{numerator}/{denominator}"


class Solution:
    def fractionAddition(self, expression: str) -> str:
        return solve(expression)
