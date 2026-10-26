"""2427. Number of Common Factors (Easy).

Specification: https://leetcode.com/problems/number-of-common-factors/description/
"""


def solve(a: int, b: int) -> int:
    """O(log(min(a,b)) + sqrt(gcd(a,b))) time, O(1) space; count divisors of the gcd."""
    first = a
    second = b
    while second:
        first, second = second, first % second
    count = 0
    divisor = 1
    while divisor * divisor <= first:
        if first % divisor == 0:
            count += 1 if divisor * divisor == first else 2
        divisor += 1
    return count


class Solution:
    def commonFactors(self, a: int, b: int) -> int:
        return solve(a, b)
