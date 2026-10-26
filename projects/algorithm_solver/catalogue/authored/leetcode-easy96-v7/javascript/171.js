'use strict';

// 171. Excel Sheet Column Number (Easy).
// Specification: https://leetcode.com/problems/excel-sheet-column-number/description/
// O(n) time, O(1) auxiliary space; accumulate the bijective base-26 value.
function solve(columnTitle) {
  let result = 0;
  for (const character of columnTitle) {
    result = result * 26 + character.charCodeAt(0) - 64;
  }
  return result;
}

const titleToNumber = solve;
class Solution {
  titleToNumber(columnTitle) { return solve(columnTitle); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, titleToNumber };
