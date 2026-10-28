'use strict';

// 59. Spiral Matrix II (Medium).
// Specification: https://leetcode.com/problems/spiral-matrix-ii/description/
function solve(n) {
  const result = Array.from({ length: n }, () => new Array(n).fill(0));
  let top = 0; let bottom = n - 1; let left = 0; let right = n - 1; let value = 1;
  while (top <= bottom && left <= right) {
    for (let c = left; c <= right; c++) result[top][c] = value++;
    top++;
    for (let r = top; r <= bottom; r++) result[r][right] = value++;
    right--;
    if (top <= bottom) { for (let c = right; c >= left; c--) result[bottom][c] = value++; bottom--; }
    if (left <= right) { for (let r = bottom; r >= top; r--) result[r][left] = value++; left++; }
  }
  return result;
}
const generateMatrix = solve;
class Solution { generateMatrix(n) { return solve(n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, generateMatrix };
