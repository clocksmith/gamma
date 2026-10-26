'use strict';

// 2022. Convert 1D Array Into 2D Array (Easy).
// Specification: https://leetcode.com/problems/convert-1d-array-into-2d-array/description/
// O(m * n) time and result space when dimensions match; preserve original and allocate fresh rows.
function solve(original, m, n) {
  if (original.length !== m * n) return [];
  const result = [];
  for (let row = 0; row < m; row++) result.push(original.slice(row * n, (row + 1) * n));
  return result;
}

const construct2DArray = solve;
class Solution {
  construct2DArray(original, m, n) { return solve(original, m, n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, construct2DArray };
