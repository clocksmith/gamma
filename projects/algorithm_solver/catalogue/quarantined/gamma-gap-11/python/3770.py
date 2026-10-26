"""3770. Largest Prime from Consecutive Prime Sum."""
from __future__ import annotations
from math import isqrt


def solve(n: int) -> int:
    """O(n log log n) time and O(n) space; sum consecutive primes beginning at 2."""
    if n < 2:
        return 0
    prime = bytearray([1]) * (n + 1)
    prime[0] = prime[1] = 0
    for divisor in range(2, isqrt(n) + 1):
        if prime[divisor]:
            for multiple in range(divisor * divisor, n + 1, divisor):
                prime[multiple] = 0
    total = answer = 0
    for value in range(2, n + 1):
        if prime[value]:
            total += value
            if total > n:
                break
            if prime[total]:
                answer = total
    return answer


class Solution:
    def largestPrime(self, n: int) -> int:
        return solve(n)
