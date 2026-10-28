'use strict';

// 1594. Maximum Non Negative Product in a Matrix (Medium).
// Specification: https://leetcode.com/problems/maximum-non-negative-product-in-a-matrix/description/
function solve(grid) {
  const MOD = 1000000007;
  const rows = grid.length; const cols = grid[0].length;
  const minDp = Array.from({ length: rows }, () => new Array(cols).fill(0));
  const maxDp = Array.from({ length: rows }, () => new Array(cols).fill(0));
  minDp[0][0] = grid[0][0]; maxDp[0][0] = grid[0][0];
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      if (r === 0 && c === 0) continue;
      const candidates = [];
      if (r > 0) { candidates.push(minDp[r - 1][c] * grid[r][c]); candidates.push(maxDp[r - 1][c] * grid[r][c]); }
      if (c > 0) { candidates.push(minDp[r][c - 1] * grid[r][c]); candidates.push(maxDp[r][c - 1] * grid[r][c]); }
      minDp[r][c] = Math.min(...candidates);
      maxDp[r][c] = Math.max(...candidates);
    }
  }
  const best = maxDp[rows - 1][cols - 1];
  return best < 0 ? -1 : best % MOD;
}
const maxProductPath = solve;
class Solution { maxProductPath(grid) { return solve(grid); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxProductPath };
