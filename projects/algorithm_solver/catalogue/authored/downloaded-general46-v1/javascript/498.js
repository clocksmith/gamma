'use strict';

// 498. Diagonal Traverse (Medium).
// Specification: https://leetcode.com/problems/diagonal-traverse/description/
function solve(mat) {
  const rows = mat.length; const cols = mat[0].length;
  const groups = {};
  for (let r = 0; r < rows; r++) { for (let c = 0; c < cols; c++) { const key = r + c; if (!groups[key]) groups[key] = []; groups[key].push(mat[r][c]); } }
  const result = [];
  for (let key = 0; key <= rows + cols - 2; key++) {
    const group = groups[key];
    if (key % 2 === 0) group.reverse();
    result.push(...group);
  }
  return result;
}
const findDiagonalOrder = solve;
class Solution { findDiagonalOrder(mat) { return solve(mat); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findDiagonalOrder };
