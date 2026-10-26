"""3881. Direction Assignments with Exactly K Visible People."""
from __future__ import annotations


def solve(n: int, pos: int, k: int) -> int:
    """O(min(k,n-1-k) + log MOD) modular steps and O(1) space; choose visible people and either direction for pos."""
    modulus = 1_000_000_007
    chosen = min(k, n - 1 - k)
    numerator = denominator = 1
    for index in range(1, chosen + 1):
        numerator = numerator * (n - index) % modulus
        denominator = denominator * index % modulus
    return 2 * numerator * pow(denominator, modulus - 2, modulus) % modulus


class Solution:
    def countAssignments(self, n: int, pos: int, k: int) -> int:
        return solve(n, pos, k)
