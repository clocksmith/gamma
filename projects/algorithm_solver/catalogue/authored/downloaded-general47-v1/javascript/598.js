'use strict';

// 598. Range Addition II (Easy).
// Specification: https://leetcode.com/problems/range-addition-ii/description/
function solve(m, n, ops) {
  if (ops.length === 0) return m * n;
  let minRow = m; let minCol = n;
  for (const [row, col] of ops) { minRow = Math.min(minRow, row); minCol = Math.min(minCol, col); }
  return minRow * minCol;
}
const maxCount = solve;
class Solution { maxCount(m, n, ops) { return solve(m, n, ops); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxCount };
