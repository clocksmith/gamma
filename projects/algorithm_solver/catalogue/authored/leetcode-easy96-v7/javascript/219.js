'use strict';

// 219. Contains Duplicate II (Easy).
// Specification: https://leetcode.com/problems/contains-duplicate-ii/description/
// O(n) expected time, O(n) space; retain the most recent index; preserve nums.
function solve(nums, k) {
  const latest = new Map();
  for (let index = 0; index < nums.length; index++) {
    const value = nums[index];
    if (latest.has(value) && index - latest.get(value) <= k) return true;
    latest.set(value, index);
  }
  return false;
}

const containsNearbyDuplicate = solve;
class Solution {
  containsNearbyDuplicate(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, containsNearbyDuplicate };
