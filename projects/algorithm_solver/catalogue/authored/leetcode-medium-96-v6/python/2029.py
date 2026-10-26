"""2029. Stone Game IX: reduce optimal play to residue counts and the parity of zero-residue moves."""


def solve(stones: list[int]) -> bool:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    counts = [0, 0, 0]
    for stone in stones:
        counts[stone % 3] += 1
    if counts[0] % 2 == 0:
        return counts[1] > 0 and counts[2] > 0
    return abs(counts[1] - counts[2]) > 2


class Solution:
    def stoneGameIX(self, stones: list[int]) -> bool:
        return solve(stones)
