"""2320. Count Number of Ways to Place Houses: count nonadjacent placements on one side and combine the independent sides."""


def solve(n: int) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    modulus = 1_000_000_007
    previous = current = 1
    for _ in range(n):
        previous, current = current, (previous + current) % modulus
    return current * current % modulus


class Solution:
    def countHousePlacements(self, n: int) -> int:
        return solve(n)
