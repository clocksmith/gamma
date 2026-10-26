"""2550. Count Collisions of Monkeys on a Polygon: subtract the two collision-free directions from all binary choices."""


def solve(n: int) -> int:
    """O(log n) modular operations and O(1) auxiliary space on the bounded integer domain; inputs are read-only."""
    modulus = 1_000_000_007
    return (pow(2, n, modulus) - 2) % modulus


class Solution:
    def monkeyMove(self, n: int) -> int:
        return solve(n)
