'use strict';

// 3779. Minimum Number of Operations to Have Distinct Elements.
// O(n) expected time and O(n) space; retain the longest duplicate-free suffix.
function solve(nums) {
  const seen = new Set();
  for (let index = nums.length - 1; index >= 0; index -= 1) {
    if (seen.has(nums[index])) return Math.floor((index + 3) / 3);
    seen.add(nums[index]);
  }
  return 0;
}

const minOperations = solve;
class Solution {
  minOperations(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minOperations };
