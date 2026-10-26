"""2312. Selling Pieces of Wood."""


def solve(m: int, n: int, prices: list[list[int]]) -> int:
    """Rectangle DP over horizontal and vertical cuts without rotation; O(m*n*(m+n)+P) time, O(m*n) space. Inputs are preserved."""
    best = [[0] * (n + 1) for _ in range(m + 1)]
    for height, width, price in prices:
        best[height][width] = max(best[height][width], price)
    for height in range(1, m + 1):
        for width in range(1, n + 1):
            for cut in range(1, height // 2 + 1):
                best[height][width] = max(best[height][width], best[cut][width] + best[height - cut][width])
            for cut in range(1, width // 2 + 1):
                best[height][width] = max(best[height][width], best[height][cut] + best[height][width - cut])
    return best[m][n]


class Solution:
    def sellingWood(self, m: int, n: int, prices: list[list[int]]) -> int:
        return solve(m, n, prices)
