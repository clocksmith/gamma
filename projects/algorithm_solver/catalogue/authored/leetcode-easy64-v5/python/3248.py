"""3248. Snake in Matrix (Easy).

Specification: https://leetcode.com/problems/snake-in-matrix/description/
"""


def solve(n: int, commands: list[str]) -> int:
    """O(number of commands) time, O(1) space; input commands are guaranteed to stay in bounds."""
    position = 0
    for command in commands:
        if command == 'UP':
            position -= n
        elif command == 'DOWN':
            position += n
        elif command == 'LEFT':
            position -= 1
        elif command == 'RIGHT':
            position += 1
    return position


class Solution:
    def finalPositionOfSnake(self, n: int, commands: list[str]) -> int:
        return solve(n, commands)
