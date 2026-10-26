'use strict';

// 2439. Minimize Maximum of Array: take the strongest ceiling-average lower bound among all prefixes.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(nums) {
  let total = 0;
  let answer = 0;
  for (let index = 0; index < nums.length; index += 1) {
    total += nums[index];
    answer = Math.max(answer, Math.floor((total + index) / (index + 1)));
  }
  return answer;
}

const minimizeArrayValue = solve;
class Solution {
  minimizeArrayValue(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimizeArrayValue };
