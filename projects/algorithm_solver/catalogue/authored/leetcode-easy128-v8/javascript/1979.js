'use strict';

// 1979. Find Greatest Common Divisor of Array (Easy).
// Specification: https://leetcode.com/problems/find-greatest-common-divisor-of-array/description/
// O(n + log M) time, O(1) space; apply Euclid to the minimum and maximum values.
function solve(nums) {
  let smallest = nums[0];
  let largest = nums[0];
  for (const value of nums) {
    smallest = Math.min(smallest, value);
    largest = Math.max(largest, value);
  }
  while (smallest !== 0) {
    const remainder = largest % smallest;
    largest = smallest;
    smallest = remainder;
  }
  return largest;
}

const findGCD = solve;
class Solution {
  findGCD(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findGCD };
