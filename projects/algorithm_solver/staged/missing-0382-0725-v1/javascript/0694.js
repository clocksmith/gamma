'use strict';

// 694. Number of Distinct Islands. Canonical translation-only coordinate signatures; preserve the grid.

function solve(grid) {
  const rows = grid.length, cols = grid[0].length, seen = new Set(), shapes = new Set();
  for (let row = 0; row < rows; row += 1) for (let col = 0; col < cols; col += 1) {
    const start = row * cols + col;
    if (grid[row][col] === 0 || seen.has(start)) continue;
    seen.add(start);
    const stack = [[row, col]], cells = [];
    while (stack.length > 0) {
      const [r, c] = stack.pop(); cells.push([r - row, c - col]);
      for (const [dr, dc] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const nr = r + dr, nc = c + dc, key = nr * cols + nc;
        if (nr >= 0 && nr < rows && nc >= 0 && nc < cols && grid[nr][nc] === 1 && !seen.has(key)) {
          seen.add(key); stack.push([nr, nc]);
        }
      }
    }
    cells.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
    shapes.add(cells.map(point => point.join(',')).join(';'));
  }
  return shapes.size;
}

const numDistinctIslands = solve;
class Solution {
  numDistinctIslands(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numDistinctIslands };
