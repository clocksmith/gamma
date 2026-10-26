"""1541. Minimum Insertions to Balance a Parentheses String: track required closing parentheses in adjacent pairs."""


def solve(s: str) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    needed = inserted = 0
    for character in s:
        if character == '(':
            if needed % 2:
                inserted += 1
                needed -= 1
            needed += 2
        else:
            needed -= 1
            if needed < 0:
                inserted += 1
                needed = 1
    return inserted + needed


class Solution:
    def minInsertions(self, s: str) -> int:
        return solve(s)
