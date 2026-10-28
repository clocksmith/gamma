'use strict';

// 378. Kth Smallest Element in a Sorted Matrix (Medium).
// Specification: https://leetcode.com/problems/kth-smallest-element-in-a-sorted-matrix/description/
function solve(matrix, k) {
  const flat = [];
  for (const row of matrix) { for (const value of row) flat.push(value); }
  flat.sort((a, b) => a - b);
  return flat[k - 1];
}
const kthSmallest = solve;
class Solution { kthSmallest(matrix, k) { return solve(matrix, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, kthSmallest };
