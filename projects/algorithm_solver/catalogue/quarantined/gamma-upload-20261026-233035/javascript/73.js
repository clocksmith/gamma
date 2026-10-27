'use strict';
// 73. Set Matrix Zeroes.
function solve(matrix) {
  const firstRow = matrix[0].some(value => value === 0);
  const firstColumn = matrix.some(row => row[0] === 0);
  for (let row = 1; row < matrix.length; row += 1) for (let column = 1; column < matrix[0].length; column += 1) {
    if (matrix[row][column] === 0) { matrix[row][0] = 0; matrix[0][column] = 0; }
  }
  for (let row = 1; row < matrix.length; row += 1) for (let column = 1; column < matrix[0].length; column += 1) {
    if (matrix[row][0] === 0 || matrix[0][column] === 0) matrix[row][column] = 0;
  }
  if (firstRow) matrix[0].fill(0);
  if (firstColumn) for (const row of matrix) row[0] = 0;
}
const setZeroes = solve;
class Solution { setZeroes(matrix) { solve(matrix); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, setZeroes };
