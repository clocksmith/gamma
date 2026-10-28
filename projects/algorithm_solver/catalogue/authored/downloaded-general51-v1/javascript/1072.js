'use strict';

// 1072. Flip Columns For Maximum Number of Equal Rows (Medium).
// Specification: https://leetcode.com/problems/flip-columns-for-maximum-number-of-equal-rows/description/
function solve(matrix) {
  const counts = new Map();
  for (const row of matrix) {
    const pattern = row[0] === 0 ? row.join('') : row.map((value) => 1 - value).join('');
    counts.set(pattern, (counts.get(pattern) || 0) + 1);
  }
  let best = 0;
  for (const count of counts.values()) best = Math.max(best, count);
  return best;
}
const maxEqualRowsAfterFlips = solve;
class Solution { maxEqualRowsAfterFlips(matrix) { return solve(matrix); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxEqualRowsAfterFlips };
