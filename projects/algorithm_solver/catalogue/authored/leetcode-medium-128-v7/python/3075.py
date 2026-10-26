"""3075. Maximize Happiness of Selected Children: select descending happiness values and subtract the number of earlier selections."""


def solve(happiness: list[int], k: int) -> int:
    """O(n log n) time and O(n) auxiliary space; inputs are read-only."""
    ordered = sorted(happiness, reverse=True)
    total = 0
    for index in range(k):
        value = ordered[index] - index
        if value <= 0:
            break
        total += value
    return total


class Solution:
    def maximumHappinessSum(self, happiness: list[int], k: int) -> int:
        return solve(happiness, k)
