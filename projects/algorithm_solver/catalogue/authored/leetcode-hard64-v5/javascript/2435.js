'use strict';

// 2435. Paths in Matrix Whose Sum Is Divisible by K. Rolling residue-count dynamic programming; O(m*n*k) time and O(n*k) space. Inputs are preserved.

function solve(grid, k) {
  const modulus = 1000000007;
  const columns = grid[0].length;
  const counts = Array.from({ length: columns }, () => Array(k).fill(0));
  for (let row = 0; row < grid.length; row += 1) {
    for (let column = 0; column < columns; column += 1) {
      const current = Array(k).fill(0);
      const value = grid[row][column] % k;
      if (row === 0 && column === 0) {
        current[value] = 1;
      } else {
        for (let remainder = 0; remainder < k; remainder += 1) {
          const ways = counts[column][remainder] + (column > 0 ? counts[column - 1][remainder] : 0);
          current[(remainder + value) % k] = ways % modulus;
        }
      }
      counts[column] = current;
    }
  }
  return counts[columns - 1][0];
}

const numberOfPaths = solve;
class Solution {
  numberOfPaths(grid, k) { return solve(grid, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfPaths };
