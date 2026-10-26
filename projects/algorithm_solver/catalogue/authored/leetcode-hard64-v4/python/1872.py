"""1872. Stone Game VIII."""


def solve(stones: list[int]) -> int:
    """Backward minimax over prefix sums; O(n) time and O(n) space. Inputs are preserved."""
    prefix = []
    total = 0
    for value in stones:
        total += value
        prefix.append(total)
    best = prefix[-1]
    for index in range(len(stones) - 2, 0, -1):
        best = max(best, prefix[index] - best)
    return best


class Solution:
    def stoneGameVIII(self, stones: list[int]) -> int:
        return solve(stones)
