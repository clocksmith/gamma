"""2944. Minimum Number of Coins for Fruits: choose the next paid fruit anywhere within or immediately beyond the current free range."""


def solve(prices: list[int]) -> int:
    """O(n * n) time and O(n) auxiliary space; inputs are read-only."""
    size = len(prices)
    best = [0] * (size + 1)
    for index in range(size - 1, -1, -1):
        following = min(best[next_index] for next_index in range(index + 1, min(size, 2 * index + 2) + 1))
        best[index] = prices[index] + following
    return best[0]


class Solution:
    def minimumCoins(self, prices: list[int]) -> int:
        return solve(prices)
