'use strict';

// 3643. Flip Square Submatrix Vertically (Easy).
// Specification: https://leetcode.com/problems/flip-square-submatrix-vertically/description/
// O(m * n + k * k) time, O(m * n) output space; preserve grid and every input row.
function solve(grid, x, y, k) {
  const result = grid.map(row => row.slice());
  for (let offset = 0; offset < Math.floor(k / 2); offset++) {
    const top = x + offset;
    const bottom = x + k - 1 - offset;
    for (let column = y; column < y + k; column++) {
      const value = result[top][column];
      result[top][column] = result[bottom][column];
      result[bottom][column] = value;
    }
  }
  return result;
}

const reverseSubmatrix = solve;
class Solution {
  reverseSubmatrix(grid, x, y, k) { return solve(grid, x, y, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, reverseSubmatrix };
