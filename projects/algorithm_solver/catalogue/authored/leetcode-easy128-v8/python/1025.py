"""1025. Divisor Game (Easy).

Specification: https://leetcode.com/problems/divisor-game/description/
"""


def solve(n: int) -> bool:
    """O(1) time and space; even starting values are winning positions under optimal play."""
    return n % 2 == 0


class Solution:
    def divisorGame(self, n: int) -> bool:
        return solve(n)
