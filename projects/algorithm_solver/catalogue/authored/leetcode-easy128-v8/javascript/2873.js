'use strict';

// 2873. Maximum Value of an Ordered Triplet I (Easy).
// Specification: https://leetcode.com/problems/maximum-value-of-an-ordered-triplet-i/description/
// O(n) time, O(1) space; update triplet, pair, then prefix to keep indices strictly ordered.
function solve(nums) {
  let largestPrefix = 0;
  let largestDifference = 0;
  let best = 0;
  for (const value of nums) {
    best = Math.max(best, largestDifference * value);
    largestDifference = Math.max(largestDifference, largestPrefix - value);
    largestPrefix = Math.max(largestPrefix, value);
  }
  return best;
}

const maximumTripletValue = solve;
class Solution {
  maximumTripletValue(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumTripletValue };
