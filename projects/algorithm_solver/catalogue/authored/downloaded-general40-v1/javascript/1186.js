'use strict';

// 1186. Maximum Subarray Sum with One Deletion (Medium).
// Specification: https://leetcode.com/problems/maximum-subarray-sum-with-one-deletion/description/
function solve(arr) {
  let without = arr[0]; let withOne = -Infinity; let best = arr[0];
  for (let i = 1; i < arr.length; i++) {
    withOne = Math.max(withOne + arr[i], without);
    without = Math.max(arr[i], without + arr[i]);
    best = Math.max(best, without, withOne);
  }
  return best;
}
const maximumSum = solve;
class Solution { maximumSum(arr) { return solve(arr); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumSum };
