"""1175. Prime Arrangements (Easy).

Specification: https://leetcode.com/problems/prime-arrangements/description/
"""


def solve(n: int) -> int:
    """O(n log log n) time, O(n) space; multiply factorial factors individually to retain exact JS integers."""
    prime = [True] * (n + 1)
    prime[0] = prime[1] = False
    value = 2
    while value * value <= n:
        if prime[value]:
            for multiple in range(value * value, n + 1, value):
                prime[multiple] = False
        value += 1
    prime_count = sum(prime)
    modulus = 1_000_000_007
    result = 1
    for factor in range(2, prime_count + 1):
        result = result * factor % modulus
    for factor in range(2, n - prime_count + 1):
        result = result * factor % modulus
    return result


class Solution:
    def numPrimeArrangements(self, n: int) -> int:
        return solve(n)
