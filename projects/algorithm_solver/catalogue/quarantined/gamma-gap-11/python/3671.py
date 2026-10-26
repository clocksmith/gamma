"""3671. Sum of Beautiful Subsequences."""
from __future__ import annotations
from math import isqrt


def solve(nums: list[int]) -> int:
    """O(M log M + n sqrt(M) + n D log M) time, O(M log M) space; D = maximum divisor count. Uses gcd = sum of totients over divisors; inputs are preserved."""
    modulus = 1_000_000_007
    maximum = max(nums)
    phi = list(range(maximum + 1))
    for prime in range(2, maximum + 1):
        if phi[prime] == prime:
            for value in range(prime, maximum + 1, prime):
                phi[value] -= phi[value] // prime
    trees = {}
    divisor_cache = {}
    answer = 0
    for value in nums:
        if value not in divisor_cache:
            divisors = []
            for divisor in range(1, isqrt(value) + 1):
                if value % divisor == 0:
                    divisors.append(divisor)
                    if divisor * divisor != value:
                        divisors.append(value // divisor)
            divisor_cache[value] = divisors
        for divisor in divisor_cache[value]:
            if divisor not in trees:
                trees[divisor] = [0] * (maximum // divisor + 1)
            tree = trees[divisor]
            coordinate = value // divisor
            index = coordinate - 1
            ways = 1
            while index > 0:
                ways = (ways + tree[index]) % modulus
                index -= index & -index
            index = coordinate
            while index < len(tree):
                tree[index] = (tree[index] + ways) % modulus
                index += index & -index
            answer = (answer + phi[divisor] * ways) % modulus
    return answer


class Solution:
    def totalBeauty(self, nums: list[int]) -> int:
        return solve(nums)
