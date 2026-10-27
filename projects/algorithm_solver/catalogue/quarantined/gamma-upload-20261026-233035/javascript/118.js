'use strict';
// 118. Pascal's Triangle.
function solve(numRows) {
  const result = [];
  for (let row = 0; row < numRows; row += 1) {
    const values = Array(row + 1).fill(1);
    for (let column = 1; column < row; column += 1) {
      values[column] = result[row - 1][column - 1] + result[row - 1][column];
    }
    result.push(values);
  }
  return result;
}
const generate = solve;
class Solution { generate(numRows) { return solve(numRows); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, generate };
