'use strict';

// 1995. Count Special Quadruplets (Easy).
// Specification: https://leetcode.com/problems/count-special-quadruplets/description/
// O(n^2) expected time, O(n^2) space; pair sums only use indices before c.
function solve(nums) {
  const pairCounts = new Map();
  let result = 0;
  for (let third = 2; third < nums.length - 1; third++) {
    const second = third - 1;
    for (let first = 0; first < second; first++) {
      const sum = nums[first] + nums[second];
      pairCounts.set(sum, (pairCounts.get(sum) || 0) + 1);
    }
    for (let fourth = third + 1; fourth < nums.length; fourth++) {
      result += pairCounts.get(nums[fourth] - nums[third]) || 0;
    }
  }
  return result;
}

const countQuadruplets = solve;
class Solution {
  countQuadruplets(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countQuadruplets };
