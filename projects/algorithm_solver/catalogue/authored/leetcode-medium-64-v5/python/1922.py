"""1922. Count Good Numbers: multiply independent even-position and odd-position choices with modular exponentiation."""


def solve(n: int) -> int:
    """O(log(n + 1)) modular multiplications and O(1) bounded auxiliary storage; inputs are read-only."""
    modulus = 1_000_000_007
    return pow(5, (n + 1) // 2, modulus) * pow(4, n // 2, modulus) % modulus


class Solution:
    def countGoodNumbers(self, n: int) -> int:
        return solve(n)
