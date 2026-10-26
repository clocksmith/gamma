"""1808. Maximize Number of Nice Divisors."""


def solve(primeFactors: int) -> int:
    """Optimal integer partition into threes and twos; O(log primeFactors) modular operations. Inputs are preserved."""
    if primeFactors <= 3:
        return primeFactors
    modulus = 1_000_000_007
    quotient, remainder = divmod(primeFactors, 3)
    if remainder == 0:
        return pow(3, quotient, modulus)
    if remainder == 1:
        return pow(3, quotient - 1, modulus) * 4 % modulus
    return pow(3, quotient, modulus) * 2 % modulus


class Solution:
    def maxNiceDivisors(self, primeFactors: int) -> int:
        return solve(primeFactors)
