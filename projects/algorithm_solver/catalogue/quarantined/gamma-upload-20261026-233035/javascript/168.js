'use strict';
// 168. Excel Sheet Column Title.
function solve(columnNumber) {
  const result = [];
  while (columnNumber > 0) {
    columnNumber -= 1;
    result.push(String.fromCharCode(65 + columnNumber % 26));
    columnNumber = Math.floor(columnNumber / 26);
  }
  return result.reverse().join('');
}
const convertToTitle = solve;
class Solution { convertToTitle(columnNumber) { return solve(columnNumber); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, convertToTitle };
