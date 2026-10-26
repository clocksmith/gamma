"""2275. Largest Combination With Bitwise AND Greater Than Zero: count supporters of each bit because a positive AND needs one shared bit."""


def solve(candidates: list[int]) -> int:
    """O(31n) time and O(1) auxiliary space on the nonnegative 31-bit domain; inputs are read-only."""
    best = 0
    for bit in range(31):
        mask = 1 << bit
        count = sum((value & mask) != 0 for value in candidates)
        best = max(best, count)
    return best


class Solution:
    def largestCombination(self, candidates: list[int]) -> int:
        return solve(candidates)
