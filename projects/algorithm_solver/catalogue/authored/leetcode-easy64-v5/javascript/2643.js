'use strict';

// 2643. Row With Maximum Ones (Easy).
// Specification: https://leetcode.com/problems/row-with-maximum-ones/description/
// O(r * c) time, O(1) auxiliary space; preserve mat; favor the first row on ties.
function solve(mat) {
  let bestRow = 0;
  let bestCount = -1;
  for (let row = 0; row < mat.length; row++) {
    let count = 0;
    for (const value of mat[row]) count += value;
    if (count > bestCount) {
      bestRow = row;
      bestCount = count;
    }
  }
  return [bestRow, bestCount];
}

const rowAndMaximumOnes = solve;
class Solution {
  rowAndMaximumOnes(mat) { return solve(mat); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, rowAndMaximumOnes };
