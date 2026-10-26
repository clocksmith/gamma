'use strict';

// 1568. Minimum Number of Days to Disconnect Island: component counting under one omitted land cell; O((rows*columns)^2) time and O(rows*columns) space.

function solve(grid) {
  const rows = grid.length;
  const columns = grid[0].length;
  const land = [];
  for (let row = 0; row < rows; row += 1) {
    for (let column = 0; column < columns; column += 1) {
      if (grid[row][column] === 1) land.push(row * columns + column);
    }
  }
  function components(omitted = -1) {
    const seen = new Set();
    let count = 0;
    for (const start of land) {
      if (start === omitted || seen.has(start)) continue;
      count += 1;
      if (count > 1) return count;
      seen.add(start);
      const stack = [start];
      while (stack.length > 0) {
        const cell = stack.pop();
        const row = Math.floor(cell / columns);
        const column = cell % columns;
        for (const [dr, dc] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
          const nr = row + dr;
          const nc = column + dc;
          if (nr < 0 || nr >= rows || nc < 0 || nc >= columns || grid[nr][nc] === 0) continue;
          const neighbor = nr * columns + nc;
          if (neighbor !== omitted && !seen.has(neighbor)) {
            seen.add(neighbor);
            stack.push(neighbor);
          }
        }
      }
    }
    return count;
  }
  if (components() !== 1) return 0;
  for (const cell of land) if (components(cell) !== 1) return 1;
  return 2;
}

const minDays = solve;
class Solution {
  minDays(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minDays };
