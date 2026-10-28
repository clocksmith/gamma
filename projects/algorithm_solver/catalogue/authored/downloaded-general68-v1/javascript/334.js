'use strict';

// 334. Increasing Triplet Subsequence (Medium).
// Specification: https://leetcode.com/problems/increasing-triplet-subsequence/description/
function solve(nums) {
  let first = Infinity; let second = Infinity;
  for (const value of nums) {
    if (value <= first) first = value;
    else if (value <= second) second = value;
    else return true;
  }
  return false;
}
const increasingTriplet = solve;
class Solution { increasingTriplet(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, increasingTriplet };
