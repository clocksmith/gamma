"""313. Super Ugly Number (Medium).

Specification: https://leetcode.com/problems/super-ugly-number/description/
"""


def solve(n: int, primes: list[int]) -> int:
    ugly = [1]
    indices = [0] * len(primes)
    while len(ugly) < n:
        nxt = min(primes[i] * ugly[indices[i]] for i in range(len(primes)))
        ugly.append(nxt)
        for i in range(len(primes)):
            if primes[i] * ugly[indices[i]] == nxt:
                indices[i] += 1
    return ugly[n - 1]


class Solution:
    def nthSuperUglyNumber(self, n: int, primes: list[int]) -> int:
        return solve(n, primes)
