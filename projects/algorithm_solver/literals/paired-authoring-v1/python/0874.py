class Solution:
    def robotSim(self, commands: list[int], obstacles: list[list[int]]) -> int:
        blocked = {(x, y) for x, y in obstacles}
        directions = ((0, 1), (1, 0), (0, -1), (-1, 0))
        heading = 0
        x = 0
        y = 0
        best = 0
        for command in commands:
            if command == -2:
                heading = (heading + 3) % 4
            elif command == -1:
                heading = (heading + 1) % 4
            else:
                x_step, y_step = directions[heading]
                for _ in range(command):
                    next_x = x + x_step
                    next_y = y + y_step
                    if (next_x, next_y) in blocked:
                        break
                    x = next_x
                    y = next_y
                    best = max(best, x * x + y * y)
        return best
