'use strict';

// 1391. Check if There is a Valid Path in a Grid: traverse only street openings whose neighboring tiles connect back.
// O(r * c) time and O(r * c) auxiliary space; inputs are read-only.
function solve(grid) {
  const openings = [[], [1, 3], [0, 2], [2, 3], [1, 2], [0, 3], [0, 1]];
  const directions = [[-1, 0], [0, 1], [1, 0], [0, -1]];
  const rows = grid.length;
  const cols = grid[0].length;
  const seen = new Uint8Array(rows * cols);
  seen[0] = 1;
  const stack = [[0, 0]];
  while (stack.length) {
    const [row, col] = stack.pop();
    if (row === rows - 1 && col === cols - 1) return true;
    for (const direction of openings[grid[row][col]]) {
      const [dr, dc] = directions[direction];
      const nextRow = row + dr;
      const nextCol = col + dc;
      if (nextRow < 0 || nextRow >= rows || nextCol < 0 || nextCol >= cols) continue;
      const index = nextRow * cols + nextCol;
      if (!seen[index] && openings[grid[nextRow][nextCol]].includes((direction + 2) % 4)) {
        seen[index] = 1;
        stack.push([nextRow, nextCol]);
      }
    }
  }
  return false;
}

const hasValidPath = solve;
class Solution {
  hasValidPath(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, hasValidPath };
