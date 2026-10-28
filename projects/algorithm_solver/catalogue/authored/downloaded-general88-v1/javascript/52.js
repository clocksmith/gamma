'use strict';

// 52. N-Queens II (Hard).
// Specification: https://leetcode.com/problems/n-queens-ii/description/
function solve(n) {
  let count = 0;
  const columns = new Set(); const diagonals = new Set(); const antiDiagonals = new Set();
  function backtrack(row) {
    if (row === n) { count++; return; }
    for (let col = 0; col < n; col++) {
      if (columns.has(col) || diagonals.has(row - col) || antiDiagonals.has(row + col)) continue;
      columns.add(col); diagonals.add(row - col); antiDiagonals.add(row + col);
      backtrack(row + 1);
      columns.delete(col); diagonals.delete(row - col); antiDiagonals.delete(row + col);
    }
  }
  backtrack(0);
  return count;
}
const totalNQueens = solve;
class Solution { totalNQueens(n) { return solve(n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, totalNQueens };
