'use strict';

// 2194. Cells in a Range on an Excel Sheet (Easy).
// Specification: https://leetcode.com/problems/cells-in-a-range-on-an-excel-sheet/description/
// O(c * r) time and result space; single-letter columns and single-digit rows; column-major order.
function solve(s) {
  const result = [];
  for (let column = s.charCodeAt(0); column <= s.charCodeAt(3); column++) {
    for (let row = Number(s[1]); row <= Number(s[4]); row++) {
      result.push(String.fromCharCode(column) + String(row));
    }
  }
  return result;
}

const cellsInRange = solve;
class Solution {
  cellsInRange(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, cellsInRange };
