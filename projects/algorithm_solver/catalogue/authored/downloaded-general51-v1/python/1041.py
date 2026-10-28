"""1041. Robot Bounded In Circle (Easy).

Specification: https://leetcode.com/problems/robot-bounded-in-circle/description/
"""


def solve(instructions: str) -> bool:
    x, y = 0, 0
    direction = 0
    moves = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    for ch in instructions:
        if ch == 'G':
            x += moves[direction][0]
            y += moves[direction][1]
        elif ch == 'L':
            direction = (direction + 3) % 4
        else:
            direction = (direction + 1) % 4
    return (x == 0 and y == 0) or direction != 0


class Solution:
    def isRobotBounded(self, instructions: str) -> bool:
        return solve(instructions)
