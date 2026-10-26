"""2580. Count Ways to Group Overlapping Ranges: count connected interval groups and choose either destination for each group."""


def solve(ranges: list[list[int]]) -> int:
    """O(n log n) time and O(n) auxiliary space; inputs are read-only."""
    modulus = 1_000_000_007
    ways = 1
    end = -1
    for left, right in sorted(ranges):
        if left > end:
            ways = ways * 2 % modulus
        end = max(end, right)
    return ways


class Solution:
    def countWays(self, ranges: list[list[int]]) -> int:
        return solve(ranges)
