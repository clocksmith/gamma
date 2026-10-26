"""1411. Number of Ways to Paint N x 3 Grid: two row-pattern classes; O(n) time and O(1) space."""


def solve(n: int) -> int:
    modulus = 1_000_000_007
    two_colors = three_colors = 6
    for _ in range(1, n):
        two_colors, three_colors = ((3 * two_colors + 2 * three_colors) % modulus,
                                    (2 * two_colors + 2 * three_colors) % modulus)
    return (two_colors + three_colors) % modulus


class Solution:
    def numOfWays(self, n: int) -> int:
        return solve(n)
