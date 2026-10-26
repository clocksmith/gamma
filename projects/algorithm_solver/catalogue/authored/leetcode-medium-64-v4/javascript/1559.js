'use strict';

// 1559. Detect Cycles in 2D Grid: detect non-parent revisits in each equal-letter grid component.
// O(r * c) time and O(r * c) auxiliary space; inputs are read-only.
function solve(grid) {
  const rows = grid.length;
  const cols = grid[0].length;
  const seen = new Uint8Array(rows * cols);
  const directions = [[-1, 0], [1, 0], [0, -1], [0, 1]];
  for (let startRow = 0; startRow < rows; startRow += 1) {
    for (let startCol = 0; startCol < cols; startCol += 1) {
      const start = startRow * cols + startCol;
      if (seen[start]) continue;
      seen[start] = 1;
      const stack = [[startRow, startCol, -1]];
      while (stack.length) {
        const [row, col, parent] = stack.pop();
        const current = row * cols + col;
        for (const [dr, dc] of directions) {
          const nextRow = row + dr;
          const nextCol = col + dc;
          if (nextRow < 0 || nextRow >= rows || nextCol < 0 || nextCol >= cols) continue;
          const following = nextRow * cols + nextCol;
          if (following === parent || grid[nextRow][nextCol] !== grid[row][col]) continue;
          if (seen[following]) return true;
          seen[following] = 1;
          stack.push([nextRow, nextCol, current]);
        }
      }
    }
  }
  return false;
}

const containsCycle = solve;
class Solution {
  containsCycle(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, containsCycle };
