'use strict';

// 3810. Minimum Operations to Reach Target Array.
// O(n) expected time and O(n) space; count distinct original values at mismatching positions.
function solve(nums, target) {
  const unfinished = new Set();
  for (let index = 0; index < nums.length; index += 1) {
    if (nums[index] !== target[index]) unfinished.add(nums[index]);
  }
  return unfinished.size;
}

const minOperations = solve;
class Solution {
  minOperations(nums, target) { return solve(nums, target); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minOperations };
