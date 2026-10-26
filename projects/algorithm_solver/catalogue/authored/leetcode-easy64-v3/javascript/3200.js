'use strict';

// 3200. Maximum Height of a Triangle (Easy).
// Specification: https://leetcode.com/problems/maximum-height-of-a-triangle/description/
// O(sqrt(red + blue)) time, O(1) space; try both starting colors.
function solve(red, blue) {
  function height(first, second) {
    let row = 1;
    while (true) {
      if (row % 2 === 1) {
        if (first < row) break;
        first -= row;
      } else {
        if (second < row) break;
        second -= row;
      }
      row++;
    }
    return row - 1;
  }
  return Math.max(height(red, blue), height(blue, red));
}

const maxHeightOfTriangle = solve;
class Solution {
  maxHeightOfTriangle(red, blue) { return solve(red, blue); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxHeightOfTriangle };
