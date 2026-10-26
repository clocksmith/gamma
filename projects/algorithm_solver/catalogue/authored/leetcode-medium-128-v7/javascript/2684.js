'use strict';

// 2684. Maximum Number of Moves in a Grid: compute longest increasing moves one column at a time from right to left.
// O(r * c) time and O(r) auxiliary space; inputs are read-only.
function solve(grid) {
  const rows = grid.length;
  const columns = grid[0].length;
  let following = new Int32Array(rows);
  for (let column = columns - 2; column >= 0; column -= 1) {
    const current = new Int32Array(rows);
    for (let row = 0; row < rows; row += 1) {
      for (let neighbor = Math.max(0, row - 1); neighbor <= Math.min(rows - 1, row + 1); neighbor += 1) {
        if (grid[neighbor][column + 1] > grid[row][column]) {
          current[row] = Math.max(current[row], following[neighbor] + 1);
        }
      }
    }
    following = current;
  }
  let best = 0;
  for (const value of following) best = Math.max(best, value);
  return best;
}

const maxMoves = solve;
class Solution {
  maxMoves(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxMoves };
