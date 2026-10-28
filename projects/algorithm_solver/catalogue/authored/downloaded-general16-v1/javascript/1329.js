'use strict';

// 1329. Sort the Matrix Diagonally (Medium).
// Specification: https://leetcode.com/problems/sort-the-matrix-diagonally/description/
function solve(mat) {
  const m = mat.length; const n = mat[0].length;
  const diagonals = new Map();
  for (let i = 0; i < m; i++) {
    for (let j = 0; j < n; j++) {
      const key = i - j;
      if (!diagonals.has(key)) diagonals.set(key, []);
      diagonals.get(key).push(mat[i][j]);
    }
  }
  for (const values of diagonals.values()) values.sort((a, b) => a - b);
  const positions = new Map();
  const answer = Array.from({ length: m }, () => new Array(n).fill(0));
  for (let i = 0; i < m; i++) {
    for (let j = 0; j < n; j++) {
      const key = i - j;
      const index = positions.get(key) || 0;
      positions.set(key, index + 1);
      answer[i][j] = diagonals.get(key)[index];
    }
  }
  return answer;
}
const diagonalSort = solve;
class Solution { diagonalSort(...args) { return solve(...args); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, diagonalSort };
