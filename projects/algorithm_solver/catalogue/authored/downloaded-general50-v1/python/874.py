"""874. Walking Robot Simulation (Medium).

Specification: https://leetcode.com/problems/walking-robot-simulation/description/
"""


def solve(commands: list[int], obstacles: list[list[int]]) -> int:
    blocked = {(x, y) for x, y in obstacles}
    dirs = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    direction = 0
    x = 0
    y = 0
    best = 0
    for cmd in commands:
        if cmd == -2:
            direction = (direction + 3) % 4
        elif cmd == -1:
            direction = (direction + 1) % 4
        else:
            for _step in range(cmd):
                nx = x + dirs[direction][0]
                ny = y + dirs[direction][1]
                if (nx, ny) in blocked:
                    break
                x, y = nx, ny
                best = max(best, x * x + y * y)
    return best


class Solution:
    def robotSim(self, commands: list[int], obstacles: list[list[int]]) -> int:
        return solve(commands, obstacles)
