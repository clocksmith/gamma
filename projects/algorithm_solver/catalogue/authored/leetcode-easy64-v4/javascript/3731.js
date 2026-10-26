'use strict';

// 3731. Find Missing Elements (Easy).
// Specification: https://leetcode.com/problems/find-missing-elements/description/
// O(n + R) expected time, O(n + R) space; R is the value range; preserve nums.
function solve(nums) {
  const present = new Set(nums);
  let smallest = nums[0];
  let largest = nums[0];
  for (const value of nums) {
    smallest = Math.min(smallest, value);
    largest = Math.max(largest, value);
  }
  const result = [];
  for (let value = smallest; value <= largest; value++) {
    if (!present.has(value)) result.push(value);
  }
  return result;
}

const findMissingElements = solve;
class Solution {
  findMissingElements(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findMissingElements };
