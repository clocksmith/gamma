"""3021. Alice and Bob Playing Flower Game: count pairs whose total number of flowers is odd."""


def solve(n: int, m: int) -> int:
    """O(1) time and O(1) auxiliary space on the bounded integer domain; inputs are read-only."""
    return ((n + 1) // 2) * (m // 2) + (n // 2) * ((m + 1) // 2)


class Solution:
    def flowerGame(self, n: int, m: int) -> int:
        return solve(n, m)
