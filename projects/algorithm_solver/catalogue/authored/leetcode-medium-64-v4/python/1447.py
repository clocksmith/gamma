"""1447. Simplified Fractions: enumerate proper fractions and retain only coprime numerator-denominator pairs."""
from math import gcd


def solve(n: int) -> list[str]:
    """O(n^2 * log(n + 1)) time and O(1) auxiliary space excluding the result; inputs are read-only."""
    result = []
    for denominator in range(2, n + 1):
        for numerator in range(1, denominator):
            if gcd(numerator, denominator) == 1:
                result.append(f'{numerator}/{denominator}')
    return result


class Solution:
    def simplifiedFractions(self, n: int) -> list[str]:
        return solve(n)
