'use strict';

// 2596. Check Knight Tour Configuration: recover positions by visit number and check every consecutive knight move.
// O(n * n) time and O(n * n) auxiliary space; inputs are read-only.
function solve(grid) {
  const size = grid.length;
  if (grid[0][0] !== 0) return false;
  const positions = new Array(size * size);
  for (let row = 0; row < size; row += 1) {
    for (let column = 0; column < size; column += 1) positions[grid[row][column]] = [row, column];
  }
  for (let step = 1; step < positions.length; step += 1) {
    const vertical = Math.abs(positions[step][0] - positions[step - 1][0]);
    const horizontal = Math.abs(positions[step][1] - positions[step - 1][1]);
    if (vertical * horizontal !== 2) return false;
  }
  return true;
}

const checkValidGrid = solve;
class Solution {
  checkValidGrid(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, checkValidGrid };
