"""1969. Minimum Non-Zero Product of the Array Elements: keep the all-ones maximum and pair the other values into one and maximum-minus-one."""


def solve(p: int) -> int:
    """O(p) modular multiplications and O(p) bits of auxiliary storage; inputs are read-only."""
    modulus = 1_000_000_007
    maximum = (1 << p) - 1
    pairs = (1 << (p - 1)) - 1
    return (maximum % modulus) * pow(maximum - 1, pairs, modulus) % modulus


class Solution:
    def minNonZeroProduct(self, p: int) -> int:
        return solve(p)
