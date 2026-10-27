'use strict';
// 48. Rotate Image.
function solve(matrix) {
  const size = matrix.length;
  for (let row = 0; row < size; row += 1) {
    for (let column = row + 1; column < size; column += 1) {
      [matrix[row][column], matrix[column][row]] = [matrix[column][row], matrix[row][column]];
    }
  }
  for (const row of matrix) row.reverse();
}
const rotate = solve;
class Solution { rotate(matrix) { solve(matrix); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, rotate };
