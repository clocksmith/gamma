"""3918. Sum of Primes Between Number and Its Reverse.

Specification: https://leetcode.com/problems/sum-of-primes-between-number-and-its-reverse/description/
"""

from __future__ import annotations


def solve(n: int) -> int:
    """O(V log log V) time and O(V) space, V=max(n, reverse(n)). Inputs are preserved."""
    reversed_number = int(str(n)[::-1])
    low, high = min(n, reversed_number), max(n, reversed_number)
    composite = bytearray(high + 1)
    prime = 2
    while prime * prime <= high:
        if not composite[prime]:
            for multiple in range(prime * prime, high + 1, prime):
                composite[multiple] = 1
        prime += 1
    return sum(value for value in range(max(2, low), high + 1) if not composite[value])
