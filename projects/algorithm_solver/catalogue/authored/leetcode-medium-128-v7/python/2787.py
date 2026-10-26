"""2787. Ways to Express an Integer as Sum of Powers: count distinct-power subsets with descending one-dimensional knapsack updates."""


def solve(n: int, x: int) -> int:
    """O(n * floor(n^(1/x))) time and O(n) auxiliary space; inputs are read-only."""
    modulus = 1_000_000_007
    ways = [0] * (n + 1)
    ways[0] = 1
    base = 1
    while base ** x <= n:
        value = base ** x
        for total in range(n, value - 1, -1):
            ways[total] = (ways[total] + ways[total - value]) % modulus
        base += 1
    return ways[n]


class Solution:
    def numberOfWays(self, n: int, x: int) -> int:
        return solve(n, x)
