"""1894. Find the Student that Will Replace the Chalk: skip complete classroom cycles."""


def solve(chalk: list[int], k: int) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    remaining = k % sum(chalk)
    for index, amount in enumerate(chalk):
        if remaining < amount:
            return index
        remaining -= amount
    return -1


class Solution:
    def chalkReplacer(self, chalk: list[int], k: int) -> int:
        return solve(chalk, k)
