'use strict';

// 1337. The K Weakest Rows in a Matrix (Easy).
// Specification: https://leetcode.com/problems/the-k-weakest-rows-in-a-matrix/description/
// O(rows * columns + rows log rows) time, O(rows) space; preserve mat.
function solve(mat, k) {
  const ranked = [];
  for (let row = 0; row < mat.length; row++) {
    let soldiers = 0;
    for (const cell of mat[row]) soldiers += cell;
    ranked.push([soldiers, row]);
  }
  ranked.sort((left, right) => left[0] - right[0] || left[1] - right[1]);
  const result = [];
  for (let index = 0; index < k; index++) result.push(ranked[index][1]);
  return result;
}

const kWeakestRows = solve;
class Solution {
  kWeakestRows(mat, k) { return solve(mat, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, kWeakestRows };
