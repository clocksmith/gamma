'use strict';

// 2862. Maximum Element-Sum of a Complete Subset of Indices. Enumerate positive square-multiple index groups; O(n) time and O(1) space; sum of floor(sqrt(n/base)) is at most 2*n. Inputs are preserved.

function solve(nums) {
  const size = nums.length;
  let answer = 0;
  for (let base = 1; base <= size; base += 1) {
    let total = 0;
    for (let multiplier = 1; base * multiplier * multiplier <= size; multiplier += 1) {
      total += nums[base * multiplier * multiplier - 1];
    }
    answer = Math.max(answer, total);
  }
  return answer;
}

const maximumSum = solve;
class Solution {
  maximumSum(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumSum };
