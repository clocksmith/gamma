"""1806. Minimum Number of Operations to Reinitialize a Permutation: follow the nontrivial index-one cycle of the perfect shuffle."""


def solve(n: int) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    position = 1
    steps = 0
    while True:
        if position % 2 == 0:
            position //= 2
        else:
            position = n // 2 + (position - 1) // 2
        steps += 1
        if position == 1:
            return steps


class Solution:
    def reinitializePermutation(self, n: int) -> int:
        return solve(n)
