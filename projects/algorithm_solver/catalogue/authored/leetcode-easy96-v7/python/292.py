"""292. Nim Game (Easy).

Specification: https://leetcode.com/problems/nim-game/description/
"""


def solve(n: int) -> bool:
    """O(1) time and space; multiples of four are losing positions."""
    return n % 4 != 0


class Solution:
    def canWinNim(self, n: int) -> bool:
        return solve(n)
