'use strict';

// 3229. Minimum Operations to Make Array Equal to Target.
// Charge each new signed layer of the difference array; O(n) time and O(1) auxiliary space. Inputs are preserved.

function solve(nums, target) {
  let previous = 0, answer = 0;
  for (let index = 0; index < nums.length; index += 1) {
    const current = target[index] - nums[index];
    const sameSign = (current > 0 && previous > 0) || (current < 0 && previous < 0);
    answer += sameSign ? Math.max(0, Math.abs(current) - Math.abs(previous)) : Math.abs(current);
    previous = current;
  }
  return answer;
}

const minimumOperations = solve;
class Solution {
  minimumOperations(nums, target) { return solve(nums, target); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumOperations };
