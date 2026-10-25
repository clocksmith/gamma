'use strict';

// 2132. Stamping the Grid.
// O(rows*cols) time and space; flat tables avoid per-row overhead on very thin grids.
function solve(grid, stampHeight, stampWidth) {
  const rows = grid.length;
  const cols = grid[0].length;
  const stride = cols + 1;
  const size = (rows + 1) * stride;
  const occupied = new Int32Array(size);
  for (let row = 0; row < rows; row += 1) {
    let running = 0;
    const previous = row * stride;
    const current = (row + 1) * stride;
    for (let col = 0; col < cols; col += 1) {
      running += grid[row][col];
      occupied[current + col + 1] = occupied[previous + col + 1] + running;
    }
  }
  const coverage = new Int32Array(size);
  for (let row = 0; row + stampHeight <= rows; row += 1) {
    const top = row * stride;
    const bottom = (row + stampHeight) * stride;
    for (let col = 0; col + stampWidth <= cols; col += 1) {
      const right = col + stampWidth;
      const count = occupied[bottom + right] - occupied[top + right]
        - occupied[bottom + col] + occupied[top + col];
      if (count === 0) {
        coverage[top + col] += 1;
        coverage[top + right] -= 1;
        coverage[bottom + col] -= 1;
        coverage[bottom + right] += 1;
      }
    }
  }
  for (let row = 0; row < rows; row += 1) {
    for (let col = 0; col < cols; col += 1) {
      const index = row * stride + col;
      if (row > 0) coverage[index] += coverage[index - stride];
      if (col > 0) coverage[index] += coverage[index - 1];
      if (row > 0 && col > 0) coverage[index] -= coverage[index - stride - 1];
      if (grid[row][col] === 0 && coverage[index] === 0) return false;
    }
  }
  return true;
}

const possibleToStamp = solve;
class Solution {
  possibleToStamp(grid, stampHeight, stampWidth) { return solve(grid, stampHeight, stampWidth); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, possibleToStamp };
