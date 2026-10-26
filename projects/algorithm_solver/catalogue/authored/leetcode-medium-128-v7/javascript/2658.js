'use strict';

// 2658. Maximum Number of Fish in a Grid: sum connected positive cells with an explicit stack and separate visitation state.
// O(r * c) time and O(r * c) auxiliary space; inputs are read-only.
function solve(grid) {
  const rows = grid.length;
  const columns = grid[0].length;
  const seen = new Uint8Array(rows * columns);
  const directions = [[-1, 0], [1, 0], [0, -1], [0, 1]];
  let best = 0;
  for (let row = 0; row < rows; row += 1) {
    for (let column = 0; column < columns; column += 1) {
      const start = row * columns + column;
      if (seen[start] || grid[row][column] === 0) continue;
      seen[start] = 1;
      const stack = [[row, column]];
      let total = 0;
      while (stack.length) {
        const [currentRow, currentColumn] = stack.pop();
        total += grid[currentRow][currentColumn];
        for (const [dr, dc] of directions) {
          const nr = currentRow + dr;
          const nc = currentColumn + dc;
          if (nr < 0 || nr >= rows || nc < 0 || nc >= columns) continue;
          const index = nr * columns + nc;
          if (!seen[index] && grid[nr][nc] > 0) {
            seen[index] = 1;
            stack.push([nr, nc]);
          }
        }
      }
      best = Math.max(best, total);
    }
  }
  return best;
}

const findMaxFish = solve;
class Solution {
  findMaxFish(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findMaxFish };
