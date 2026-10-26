"""2145. Count the Hidden Sequences: intersect the allowed starting values implied by the prefix-sum extremes."""


def solve(differences: list[int], lower: int, upper: int) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    current = lowest = highest = 0
    for difference in differences:
        current += difference
        lowest = min(lowest, current)
        highest = max(highest, current)
    return max(0, upper - lower - (highest - lowest) + 1)


class Solution:
    def numberOfArrays(self, differences: list[int], lower: int, upper: int) -> int:
        return solve(differences, lower, upper)
