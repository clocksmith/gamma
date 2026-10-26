'use strict';

// 169. Majority Element (Easy).
// Specification: https://leetcode.com/problems/majority-element/description/
// O(n) time, O(1) space; Boyer-Moore voting under the guaranteed-majority contract.
function solve(nums) {
  let candidate = 0;
  let balance = 0;
  for (const value of nums) {
    if (balance === 0) candidate = value;
    balance += value === candidate ? 1 : -1;
  }
  return candidate;
}

const majorityElement = solve;
class Solution {
  majorityElement(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, majorityElement };
