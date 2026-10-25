'use strict';

// 2475. Number of Unequal Triplets in Array (Easy).
// Specification: https://leetcode.com/problems/number-of-unequal-triplets-in-array/description/
// O(n) expected time, O(u) space for u distinct values. Preserve nums.
function solve(nums) {
  const counts = new Map();
  for (const value of nums) counts.set(value, (counts.get(value) || 0) + 1);
  let before = 0;
  let after = nums.length;
  let result = 0;
  for (const count of counts.values()) {
    after -= count;
    result += before * count * after;
    before += count;
  }
  return result;
}

const unequalTriplets = solve;
class Solution {
  unequalTriplets(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, unequalTriplets };
