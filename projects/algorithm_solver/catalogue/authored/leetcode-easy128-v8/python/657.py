"""657. Robot Return to Origin (Easy).

Specification: https://leetcode.com/problems/robot-return-to-origin/description/
"""


def solve(moves: str) -> bool:
    """O(n) time, O(1) space; accumulate horizontal and vertical displacement."""
    horizontal = vertical = 0
    for move in moves:
        if move == 'L':
            horizontal -= 1
        elif move == 'R':
            horizontal += 1
        elif move == 'U':
            vertical += 1
        else:
            vertical -= 1
    return horizontal == 0 and vertical == 0


class Solution:
    def judgeCircle(self, moves: str) -> bool:
        return solve(moves)
