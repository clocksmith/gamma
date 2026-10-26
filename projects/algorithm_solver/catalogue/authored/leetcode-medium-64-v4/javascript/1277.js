'use strict';

// 1277. Count Square Submatrices with All Ones: roll square-size dynamic programming through one row.
// O(r * c) time and O(c) auxiliary space; inputs are read-only.
function solve(matrix) {
  const sizes = new Int32Array(matrix[0].length + 1);
  let total = 0;
  for (const row of matrix) {
    let diagonal = 0;
    for (let col = 1; col <= row.length; col += 1) {
      const above = sizes[col];
      sizes[col] = row[col - 1] ? 1 + Math.min(above, sizes[col - 1], diagonal) : 0;
      total += sizes[col];
      diagonal = above;
    }
  }
  return total;
}

const countSquares = solve;
class Solution {
  countSquares(matrix) { return solve(matrix); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countSquares };
