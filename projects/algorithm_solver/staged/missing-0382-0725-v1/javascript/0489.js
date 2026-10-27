'use strict';

// 489. Robot Room Cleaner. Use only the supplied Robot API; clean reachable cells and restore the starting position and orientation.

function solve(robot) {
  const directions = [[-1, 0], [0, 1], [1, 0], [0, -1]];
  const visited = new Set(['0,0']), stack = [[0, 0, 0, 0]];
  robot.clean();
  while (stack.length > 0) {
    const frame = stack[stack.length - 1], [row, col, initial, attempt] = frame;
    if (attempt === 4) {
      stack.pop();
      if (stack.length > 0) {
        robot.turnRight(); robot.turnRight(); robot.move();
        robot.turnRight(); robot.turnRight(); robot.turnRight();
        stack[stack.length - 1][3] += 1;
      }
      continue;
    }
    const facing = (initial + attempt) % 4, [dr, dc] = directions[facing];
    const nr = row + dr, nc = col + dc, key = `${nr},${nc}`;
    if (!visited.has(key) && robot.move()) {
      visited.add(key); robot.clean(); stack.push([nr, nc, facing, 0]);
    } else { robot.turnRight(); frame[3] += 1; }
  }
}

const cleanRoom = solve;
class Solution {
  cleanRoom(robot) { return solve(robot); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, cleanRoom };
