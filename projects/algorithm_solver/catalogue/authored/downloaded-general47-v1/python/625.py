"""625. Minimum Factorization (Medium).

Specification: https://leetcode.com/problems/minimum-factorization/description/
"""


def solve(a: int) -> int:
    if a < 10:
        return a
    digits = []
    value = a
    for divisor in range(9, 1, -1):
        while value % divisor == 0:
            digits.append(divisor)
            value //= divisor
    if value != 1:
        return 0
    digits.sort()
    result = int("".join(str(d) for d in digits))
    return 0 if result > 2147483647 else result


class Solution:
    def smallestFactorization(self, a: int) -> int:
        return solve(a)
