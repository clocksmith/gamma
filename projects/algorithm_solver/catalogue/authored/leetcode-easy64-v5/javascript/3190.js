'use strict';

// 3190. Find Minimum Operations to Make All Elements Divisible by Three (Easy).
// Specification: https://leetcode.com/problems/find-minimum-operations-to-make-all-elements-divisible-by-three/description/
// O(n) time, O(1) auxiliary space; each nonmultiple needs exactly one operation.
function solve(nums) {
  let operations = 0;
  for (const value of nums) {
    if (value % 3 !== 0) operations++;
  }
  return operations;
}

const minimumOperations = solve;
class Solution {
  minimumOperations(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumOperations };
