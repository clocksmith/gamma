'use strict';

// 1926. Nearest Exit from Entrance in Maze: search outward by distance without changing walls or counting the entrance as an exit.
// O(rows * columns) time and O(rows * columns) auxiliary space; inputs are read-only.
function solve(maze, entrance) {
  const rows = maze.length;
  const columns = maze[0].length;
  const distance = new Int32Array(rows * columns).fill(-1);
  const start = entrance[0] * columns + entrance[1];
  const queue = new Int32Array(rows * columns);
  queue[0] = start;
  distance[start] = 0;
  let head = 0;
  let tail = 1;
  const directions = [[1, 0], [-1, 0], [0, 1], [0, -1]];
  while (head < tail) {
    const cell = queue[head];
    head += 1;
    const row = Math.floor(cell / columns);
    const column = cell % columns;
    if (cell !== start && (row === 0 || row === rows - 1 || column === 0 || column === columns - 1)) {
      return distance[cell];
    }
    for (const [dr, dc] of directions) {
      const nr = row + dr;
      const nc = column + dc;
      if (nr < 0 || nr >= rows || nc < 0 || nc >= columns || maze[nr][nc] !== '.') continue;
      const neighbor = nr * columns + nc;
      if (distance[neighbor] !== -1) continue;
      distance[neighbor] = distance[cell] + 1;
      queue[tail] = neighbor;
      tail += 1;
    }
  }
  return -1;
}

const nearestExit = solve;
class Solution {
  nearestExit(maze, entrance) { return solve(maze, entrance); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, nearestExit };
