"""2761. Prime Pairs With Target Sum: sieve primality once and enumerate the smaller endpoint of each pair."""


def solve(n: int) -> list[list[int]]:
    """O(n log log(n + 2)) time and O(n) auxiliary space; inputs are read-only."""
    prime = bytearray([1]) * (n + 1)
    prime[0] = 0
    if n >= 1:
        prime[1] = 0
    factor = 2
    while factor * factor <= n:
        if prime[factor]:
            for multiple in range(factor * factor, n + 1, factor):
                prime[multiple] = 0
        factor += 1
    return [[left, n - left] for left in range(2, n // 2 + 1) if prime[left] and prime[n - left]]


class Solution:
    def findPrimePairs(self, n: int) -> list[list[int]]:
        return solve(n)
