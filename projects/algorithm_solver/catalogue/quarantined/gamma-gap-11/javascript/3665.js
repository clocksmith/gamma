'use strict';

// 3665. Twisted Mirror Path Count.
// O(rows * columns) time and O(columns) auxiliary space; inputs are preserved.
function solve(grid) {
  const modulus = 1000000007;
  const columns = grid[0].length;
  const down = Array(columns).fill(0);
  down[0] = 1;
  for (const row of grid) {
    let right = 0;
    for (let column = 0; column < columns; column += 1) {
      const above = down[column];
      if (row[column] === 1) {
        down[column] = right;
        right = above;
      } else {
        const ways = (above + right) % modulus;
        down[column] = ways;
        right = ways;
      }
    }
  }
  return down[columns - 1];
}

const uniquePaths = solve;
class Solution {
  uniquePaths(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, uniquePaths };
