"""1573. Number of Ways to Split a String: count the two gaps separating equal groups of ones."""


def solve(s: str) -> int:
    """O(n) time and O(n) auxiliary space; inputs are read-only."""
    modulus = 1_000_000_007
    ones = [index for index, character in enumerate(s) if character == "1"]
    if len(ones) % 3:
        return 0
    if not ones:
        return ((len(s) - 1) * (len(s) - 2) // 2) % modulus
    group = len(ones) // 3
    first_gap = ones[group] - ones[group - 1]
    second_gap = ones[2 * group] - ones[2 * group - 1]
    return first_gap * second_gap % modulus


class Solution:
    def numWays(self, s: str) -> int:
        return solve(s)
