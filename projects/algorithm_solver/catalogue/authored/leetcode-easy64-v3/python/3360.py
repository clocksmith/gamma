"""3360. Stone Removal Game (Easy).

Specification: https://leetcode.com/problems/stone-removal-game/description/
"""


def solve(n: int) -> bool:
    """O(1) time and space under 1 <= n <= 50; count successful alternating moves."""
    removal = 10
    alice_wins = False
    while removal > 0 and n >= removal:
        n -= removal
        removal -= 1
        alice_wins = not alice_wins
    return alice_wins


class Solution:
    def canAliceWin(self, n: int) -> bool:
        return solve(n)
