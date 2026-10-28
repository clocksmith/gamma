'use strict';

// 2556. Disconnect Path in a Binary Matrix by at Most One Flip (Medium).
// Specification: https://leetcode.com/problems/disconnect-path-in-a-binary-matrix-by-at-most-one-flip/description/
function solve(grid) {
  const g = grid.map((row) => row.slice());
  const m = g.length; const n = g[0].length;
  function dfs(i, j) {
    if (i >= m || j >= n || g[i][j] !== 1) return false;
    if (i === m - 1 && j === n - 1) return true;
    g[i][j] = 0;
    return dfs(i + 1, j) || dfs(i, j + 1);
  }
  const a = dfs(0, 0);
  g[0][0] = 1; g[m - 1][n - 1] = 1;
  const b = dfs(0, 0);
  return !(a && b);
}
const isPossibleToCutPath = solve;
class Solution { isPossibleToCutPath(grid) { return solve(grid); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, isPossibleToCutPath };
