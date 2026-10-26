'use strict';

// 3071. Minimum Operations to Write the Letter Y on a Grid: count colors inside and outside the Y and choose two distinct target colors.
// O(n * n) time and O(1) auxiliary space; inputs are read-only.
function solve(grid) {
  const size = grid.length;
  const middle = Math.floor(size / 2);
  const inside = [0, 0, 0];
  const outside = [0, 0, 0];
  for (let row = 0; row < size; row += 1) {
    for (let column = 0; column < size; column += 1) {
      const belongs = (row < middle && (column === row || column === size - 1 - row))
        || (row >= middle && column === middle);
      const counts = belongs ? inside : outside;
      counts[grid[row][column]] += 1;
    }
  }
  let retained = 0;
  for (let first = 0; first < 3; first += 1) {
    for (let second = 0; second < 3; second += 1) {
      if (first !== second) retained = Math.max(retained, inside[first] + outside[second]);
    }
  }
  return size * size - retained;
}

const minimumOperationsToWriteY = solve;
class Solution {
  minimumOperationsToWriteY(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumOperationsToWriteY };
