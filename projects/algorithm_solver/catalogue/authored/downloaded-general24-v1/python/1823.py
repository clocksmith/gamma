"""1823. Find the Winner of the Circular Game (Medium).

Specification: https://leetcode.com/problems/find-the-winner-of-the-circular-game/description/
"""


def solve(n: int, k: int) -> int:
    winner = 0
    for people in range(2, n + 1):
        winner = (winner + k) % people
    return winner + 1


class Solution:
    def findTheWinner(self, n: int, k: int) -> int:
        return solve(n, k)
