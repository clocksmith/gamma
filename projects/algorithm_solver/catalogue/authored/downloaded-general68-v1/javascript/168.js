'use strict';

// 168. Excel Sheet Column Title (Easy).
// Specification: https://leetcode.com/problems/excel-sheet-column-title/description/
function solve(columnNumber) {
  let result = '';
  let value = columnNumber;
  while (value > 0) {
    value--;
    result = String.fromCharCode(65 + (value % 26)) + result;
    value = Math.floor(value / 26);
  }
  return result;
}
const convertToTitle = solve;
class Solution { convertToTitle(columnNumber) { return solve(columnNumber); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, convertToTitle };
