'use strict';

// 119. Pascal's Triangle II (Easy).
// Specification: https://leetcode.com/problems/pascals-triangle-ii/description/
function solve(rowIndex) {
  let row = [1];
  for (let i = 1; i <= rowIndex; i++) {
    const next = new Array(i + 1).fill(1);
    for (let col = 1; col < i; col++) next[col] = row[col - 1] + row[col];
    row = next;
  }
  return row;
}
const getRow = solve;
class Solution { getRow(rowIndex) { return solve(rowIndex); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, getRow };
