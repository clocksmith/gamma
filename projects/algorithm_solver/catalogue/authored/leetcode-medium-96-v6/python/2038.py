"""2038. Remove Colored Pieces if Both Neighbors are the Same Color: count the removable interior pieces in each color run."""


def solve(colors: str) -> bool:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    alice = bob = 0
    for index in range(1, len(colors) - 1):
        if colors[index - 1] == colors[index] == colors[index + 1]:
            if colors[index] == 'A':
                alice += 1
            else:
                bob += 1
    return alice > bob


class Solution:
    def winnerOfGame(self, colors: str) -> bool:
        return solve(colors)
