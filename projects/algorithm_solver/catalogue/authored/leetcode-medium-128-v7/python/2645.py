"""2645. Minimum Additions to Make Valid String: start a new abc block whenever the next letter does not increase."""


def solve(word: str) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    blocks = 1
    for index in range(1, len(word)):
        if word[index] <= word[index - 1]:
            blocks += 1
    return 3 * blocks - len(word)


class Solution:
    def addMinimum(self, word: str) -> int:
        return solve(word)
