"""3222. Find the Winning Player in Coin Game (Easy).

Specification: https://leetcode.com/problems/find-the-winning-player-in-coin-game/description/
"""


def solve(x: int, y: int) -> str:
    """O(1) time and space; each legal turn consumes one 75-value and four 10-value coins."""
    turns = min(x, y // 4)
    return 'Alice' if turns % 2 else 'Bob'


class Solution:
    def losingPlayer(self, x: int, y: int) -> str:
        return solve(x, y)
