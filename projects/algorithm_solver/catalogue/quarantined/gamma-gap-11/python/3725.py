"""3725. Count Ways to Choose Coprime Integers from Rows."""
from __future__ import annotations
from collections import Counter
from math import gcd


def solve(mat: list[list[int]]) -> int:
    """O(M^2 log M + rows * M * columns) time and O(M^2) space; M <= 150."""
    modulus = 1_000_000_007
    maximum = max(max(row) for row in mat)
    gcds = [[gcd(left, right) for right in range(maximum + 1)] for left in range(maximum + 1)]
    ways = [0] * (maximum + 1)
    ways[0] = 1
    for row in mat:
        frequency = Counter(row)
        following = [0] * (maximum + 1)
        for previous, count in enumerate(ways):
            if count:
                for value, occurrences in frequency.items():
                    key = gcds[previous][value]
                    following[key] = (following[key] + count * occurrences) % modulus
        ways = following
    return ways[1]


class Solution:
    def countCoprime(self, mat: list[list[int]]) -> int:
        return solve(mat)
