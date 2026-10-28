'use strict';

// 3240. Minimum Number of Flips to Make Binary Grid Palindromic II (Medium).
// Specification: https://leetcode.com/problems/minimum-number-of-flips-to-make-binary-grid-palindromic-ii/description/
function solve(grid) {
  const m = grid.length; const n = grid[0].length;
  let ans = 0; let middleOnes = 0; let mismatched = 0;
  for (let i = 0; i < Math.floor(m / 2); i++)
    for (let j = 0; j < Math.floor(n / 2); j++) {
      const ones = grid[i][j] + grid[i][n - 1 - j] + grid[m - 1 - i][j] + grid[m - 1 - i][n - 1 - j];
      ans += Math.min(ones, 4 - ones);
    }
  if (m % 2 === 1) {
    const mid = Math.floor(m / 2);
    for (let j = 0; j < Math.floor(n / 2); j++) {
      const a = grid[mid][j]; const b = grid[mid][n - 1 - j];
      mismatched += a ^ b; middleOnes += a + b;
    }
  }
  if (n % 2 === 1) {
    const mid = Math.floor(n / 2);
    for (let i = 0; i < Math.floor(m / 2); i++) {
      const a = grid[i][mid]; const b = grid[m - 1 - i][mid];
      mismatched += a ^ b; middleOnes += a + b;
    }
  }
  if (mismatched === 0) {
    if (middleOnes % 4 === 2) ans += 2;
  } else {
    ans += mismatched;
  }
  if (m % 2 === 1 && n % 2 === 1) ans += grid[Math.floor(m / 2)][Math.floor(n / 2)];
  return ans;
}
const minFlips = solve;
class Solution { minFlips(grid) { return solve(grid); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, minFlips };
