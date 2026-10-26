"""2660. Determine the Winner of a Bowling Game (Easy).

Specification: https://leetcode.com/problems/determine-the-winner-of-a-bowling-game/description/
"""


def solve(player1: list[int], player2: list[int]) -> int:
    """O(n) time, O(1) space; either of the previous two strikes doubles a turn once."""
    def score(player: list[int]) -> int:
        total = 0
        for index, pins in enumerate(player):
            doubled = ((index >= 1 and player[index - 1] == 10) or
                       (index >= 2 and player[index - 2] == 10))
            total += pins * (2 if doubled else 1)
        return total

    first, second = score(player1), score(player2)
    if first == second:
        return 0
    return 1 if first > second else 2


class Solution:
    def isWinner(self, player1: list[int], player2: list[int]) -> int:
        return solve(player1, player2)
