'use strict';

// 1526. Minimum Number of Increments on Subarrays to Form a Target Array (Hard).
// Specification: https://leetcode.com/problems/minimum-number-of-increments-on-subarrays-to-form-a-target-array/description/
function solve(target) {
  let operations = target[0];
  for (let i = 1; i < target.length; i++) {
    if (target[i] > target[i - 1]) operations += target[i] - target[i - 1];
  }
  return operations;
}
const minNumberOperations = solve;
class Solution { minNumberOperations(target) { return solve(target); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, minNumberOperations };
