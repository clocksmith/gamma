'use strict';

// 2906. Construct Product Matrix: combine exclusive prefix and suffix products without modular division.
// O(r * c) time and O(r * c) auxiliary space including the result; inputs are read-only.
function solve(grid) {
  const modulus = 12345;
  const rows = grid.length;
  const columns = grid[0].length;
  const result = Array.from({ length: rows }, () => new Array(columns));
  let prefix = 1;
  for (let row = 0; row < rows; row += 1) {
    for (let column = 0; column < columns; column += 1) {
      result[row][column] = prefix;
      prefix = prefix * (grid[row][column] % modulus) % modulus;
    }
  }
  let suffix = 1;
  for (let row = rows - 1; row >= 0; row -= 1) {
    for (let column = columns - 1; column >= 0; column -= 1) {
      result[row][column] = result[row][column] * suffix % modulus;
      suffix = suffix * (grid[row][column] % modulus) % modulus;
    }
  }
  return result;
}

const constructProductMatrix = solve;
class Solution {
  constructProductMatrix(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, constructProductMatrix };
