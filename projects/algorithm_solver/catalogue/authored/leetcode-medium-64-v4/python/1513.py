"""1513. Number of Substrings With Only 1s: add the length of the current run of ones at each position."""


def solve(s: str) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    modulus = 1_000_000_007
    run = total = 0
    for bit in s:
        run = run + 1 if bit == '1' else 0
        total = (total + run) % modulus
    return total


class Solution:
    def numSub(self, s: str) -> int:
        return solve(s)
