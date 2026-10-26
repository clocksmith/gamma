'use strict';

// 2366. Minimum Replacements to Sort the Array. Greedily split from right to left; O(n) time and O(1) space. Inputs are preserved.

function solve(nums) {
  let bound = nums[nums.length - 1];
  let answer = 0;
  for (let index = nums.length - 2; index >= 0; index -= 1) {
    const value = nums[index];
    const parts = Math.floor((value + bound - 1) / bound);
    answer += parts - 1;
    bound = Math.floor(value / parts);
  }
  return answer;
}

const minimumReplacement = solve;
class Solution {
  minimumReplacement(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumReplacement };
