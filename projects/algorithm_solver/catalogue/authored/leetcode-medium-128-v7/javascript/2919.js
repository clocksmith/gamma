'use strict';

// 2919. Minimum Increment Operations to Make Array Beautiful: ensure every length-three window contains a raised element using three rolling costs.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(nums, k) {
  let first = 0;
  let second = 0;
  let third = 0;
  for (const value of nums) {
    const current = Math.min(first, second, third) + Math.max(0, k - value);
    first = second;
    second = third;
    third = current;
  }
  return Math.min(first, second, third);
}

const minIncrementOperations = solve;
class Solution {
  minIncrementOperations(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minIncrementOperations };
