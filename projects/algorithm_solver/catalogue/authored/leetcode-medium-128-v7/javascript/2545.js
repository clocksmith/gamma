'use strict';

// 2545. Sort the Students by Their Kth Score: sort independently copied rows by descending kth score.
// O(r log r + r * c) time and O(r * c) auxiliary space; inputs are read-only.
function solve(score, k) {
  return score.map(row => row.slice()).sort((left, right) => right[k] - left[k]);
}

const sortTheStudents = solve;
class Solution {
  sortTheStudents(score, k) { return solve(score, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, sortTheStudents };
