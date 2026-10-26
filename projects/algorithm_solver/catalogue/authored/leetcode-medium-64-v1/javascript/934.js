'use strict';

// 934. Shortest Bridge: flood one island then expand a multi-source breadth-first search.
// O(rows * columns) time and O(rows * columns) auxiliary space; inputs are read-only.
function solve(grid) {
  const rows = grid.length;
  const columns = grid[0].length;
  const seen = Array.from({ length: rows }, () => new Uint8Array(columns));
  const directions = [[1, 0], [-1, 0], [0, 1], [0, -1]];
  let start = null;
  for (let row = 0; row < rows && start === null; row += 1) {
    for (let column = 0; column < columns; column += 1) {
      if (grid[row][column] === 1) { start = [row, column]; break; }
    }
  }
  if (start === null) return -1;
  const stack = [start];
  const queue = [];
  seen[start[0]][start[1]] = 1;
  while (stack.length) {
    const [row, column] = stack.pop();
    queue.push([row, column]);
    for (const [dr, dc] of directions) {
      const nr = row + dr;
      const nc = column + dc;
      if (nr >= 0 && nr < rows && nc >= 0 && nc < columns && !seen[nr][nc] && grid[nr][nc] === 1) {
        seen[nr][nc] = 1;
        stack.push([nr, nc]);
      }
    }
  }
  let head = 0;
  let distance = 0;
  while (head < queue.length) {
    const layerEnd = queue.length;
    while (head < layerEnd) {
      const [row, column] = queue[head++];
      for (const [dr, dc] of directions) {
        const nr = row + dr;
        const nc = column + dc;
        if (nr >= 0 && nr < rows && nc >= 0 && nc < columns && !seen[nr][nc]) {
          if (grid[nr][nc] === 1) return distance;
          seen[nr][nc] = 1;
          queue.push([nr, nc]);
        }
      }
    }
    distance += 1;
  }
  return -1;
}

const shortestBridge = solve;
class Solution {
  shortestBridge(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, shortestBridge };
