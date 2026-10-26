'use strict';

// 3912. Valid Elements in an Array (Easy).
// Specification: https://leetcode.com/problems/valid-elements-in-an-array/description/
// O(n) time and space; strict records on either side qualify; preserve order, duplicates, and inputs.
function solve(nums) {
  const valid = new Array(nums.length).fill(false);
  let maximum = -Infinity;
  for (let index = 0; index < nums.length; index++) {
    if (nums[index] > maximum) valid[index] = true;
    maximum = Math.max(maximum, nums[index]);
  }
  maximum = -Infinity;
  for (let index = nums.length - 1; index >= 0; index--) {
    if (nums[index] > maximum) valid[index] = true;
    maximum = Math.max(maximum, nums[index]);
  }
  const result = [];
  for (let index = 0; index < nums.length; index++) {
    if (valid[index]) result.push(nums[index]);
  }
  return result;
}

const findValidElements = solve;
class Solution {
  findValidElements(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findValidElements };
