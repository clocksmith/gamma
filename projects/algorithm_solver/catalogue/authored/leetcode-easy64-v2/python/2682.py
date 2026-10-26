"""2682. Find the Losers of the Circular Game (Easy).

Specification: https://leetcode.com/problems/find-the-losers-of-the-circular-game/description/
"""


def solve(n: int, k: int) -> list[int]:
    """O(n) time, O(n) space; stop on the first repeated recipient."""
    visited = [False] * n
    current, turn = 0, 1
    while not visited[current]:
        visited[current] = True
        current = (current + turn * k) % n
        turn += 1
    return [index + 1 for index in range(n) if not visited[index]]


class Solution:
    def circularGameLosers(self, n: int, k: int) -> list[int]:
        return solve(n, k)
