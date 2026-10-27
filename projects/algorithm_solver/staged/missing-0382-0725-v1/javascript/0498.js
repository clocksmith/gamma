'use strict';

// 498. Diagonal Traverse.

function solve(mat) {
  const rows = mat.length, cols = mat[0].length, answer = [];
  for (let diagonal = 0; diagonal < rows + cols - 1; diagonal += 1) {
    const first = Math.max(0, diagonal - cols + 1), last = Math.min(rows - 1, diagonal);
    if (diagonal % 2 === 0) {
      for (let row = last; row >= first; row -= 1) answer.push(mat[row][diagonal - row]);
    } else for (let row = first; row <= last; row += 1) answer.push(mat[row][diagonal - row]);
  }
  return answer;
}

const findDiagonalOrder = solve;
class Solution {
  findDiagonalOrder(mat) { return solve(mat); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findDiagonalOrder };
