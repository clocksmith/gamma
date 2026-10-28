'use strict';

// 118. Pascal's Triangle (Easy).
// Specification: https://leetcode.com/problems/pascals-triangle/description/
function solve(numRows) {
  const result = [];
  for (let row = 0; row < numRows; row++) {
    const current = new Array(row + 1).fill(1);
    for (let col = 1; col < row; col++) current[col] = result[row - 1][col - 1] + result[row - 1][col];
    result.push(current);
  }
  return result;
}
const generate = solve;
class Solution { generate(numRows) { return solve(numRows); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, generate };
