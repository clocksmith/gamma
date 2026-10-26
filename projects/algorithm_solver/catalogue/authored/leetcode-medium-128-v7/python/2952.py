"""2952. Minimum Number of Coins to be Added: extend the covered prefix of sums and add its first missing value when necessary."""


def solve(coins: list[int], target: int) -> int:
    """O(n log n + log(target + 1)) time and O(n) auxiliary space; inputs are read-only."""
    ordered = sorted(coins)
    missing = 1
    index = added = 0
    while missing <= target:
        if index < len(ordered) and ordered[index] <= missing:
            missing += ordered[index]
            index += 1
        else:
            missing *= 2
            added += 1
    return added


class Solution:
    def minimumAddedCoins(self, coins: list[int], target: int) -> int:
        return solve(coins, target)
