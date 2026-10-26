"""2601. Prime Subtraction Operation: greedily choose the smallest feasible next value using a sieve and predecessor search."""
from bisect import bisect_left
from math import isqrt


def solve(nums: list[int]) -> bool:
    """O(M * log(log(M + 2)) + n * log(M + 1)) time and O(M) space for M = max(nums); inputs are read-only."""
    maximum = max(nums)
    is_prime = [True] * (maximum + 1)
    is_prime[0] = is_prime[1] = False
    for factor in range(2, isqrt(maximum) + 1):
        if is_prime[factor]:
            for multiple in range(factor * factor, maximum + 1, factor):
                is_prime[multiple] = False
    primes = [value for value in range(2, maximum + 1) if is_prime[value]]
    previous = 0
    for original in nums:
        position = bisect_left(primes, original - previous) - 1
        value = original - primes[position] if position >= 0 else original
        if value <= previous:
            return False
        previous = value
    return True


class Solution:
    def primeSubOperation(self, nums: list[int]) -> bool:
        return solve(nums)
