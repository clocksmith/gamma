"""3238. Find the Number of Winning Players (Easy).

Specification: https://leetcode.com/problems/find-the-number-of-winning-players/description/
"""


def solve(n: int, pick: list[list[int]]) -> int:
    """O(n + picks) time, O(n) space for the fixed eleven-color domain; preserve pick."""
    counts = [[0] * 11 for _ in range(n)]
    for player, color in pick:
        counts[player][color] += 1
    winners = 0
    for player in range(n):
        for count in counts[player]:
            if count > player:
                winners += 1
                break
    return winners


class Solution:
    def winningPlayerCount(self, n: int, pick: list[list[int]]) -> int:
        return solve(n, pick)
