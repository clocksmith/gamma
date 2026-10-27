"""489. Robot Room Cleaner. Use only the supplied Robot API; clean reachable cells and restore the starting position and orientation."""

def solve(robot):
    # Each frame owns its entry direction and the next one of four directions to try.
    directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
    visited = {(0, 0)}
    stack = [[0, 0, 0, 0]]
    robot.clean()
    while stack:
        row, col, initial, attempt = stack[-1]
        if attempt == 4:
            stack.pop()
            if stack:
                robot.turnRight()
                robot.turnRight()
                robot.move()
                robot.turnRight()
                robot.turnRight()
                robot.turnRight()
                stack[-1][3] += 1
            continue
        facing = (initial + attempt) % 4
        dr, dc = directions[facing]
        following = (row + dr, col + dc)
        if following not in visited and robot.move():
            visited.add(following)
            robot.clean()
            stack.append([following[0], following[1], facing, 0])
        else:
            robot.turnRight()
            stack[-1][3] += 1


class Solution:
    def cleanRoom(self, robot):
        return solve(robot)
