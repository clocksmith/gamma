'use strict';

// 1437. Check If All 1's Are at Least Length K Places Away (Easy).
// Specification: https://leetcode.com/problems/check-if-all-1s-are-at-least-length-k-places-away/description/
// O(n) time, O(1) space; require at least k zeros between ones; preserve nums.
function solve(nums, k) {
  let previous = -k - 1;
  for (let index = 0; index < nums.length; index++) {
    if (nums[index] === 1) {
      if (index - previous <= k) return false;
      previous = index;
    }
  }
  return true;
}

const kLengthApart = solve;
class Solution {
  kLengthApart(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, kLengthApart };
