'use strict';
// 119. Pascal's Triangle II.
function solve(rowIndex) {
  const row = Array(rowIndex + 1).fill(1);
  for (let index = 1; index < rowIndex; index += 1) {
    row[index] = row[index - 1] * (rowIndex - index + 1) / index;
  }
  return row;
}
const getRow = solve;
class Solution { getRow(rowIndex) { return solve(rowIndex); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, getRow };
