'use strict';

// 2444. Count Subarrays With Fixed Bounds. Track the last invalid value and both required endpoints; O(n) time and O(1) space. Inputs are preserved.

function solve(nums, minK, maxK) {
  let invalid = -1;
  let minimum = -1;
  let maximum = -1;
  let answer = 0;
  for (let index = 0; index < nums.length; index += 1) {
    const value = nums[index];
    if (value < minK || value > maxK) invalid = index;
    if (value === minK) minimum = index;
    if (value === maxK) maximum = index;
    answer += Math.max(0, Math.min(minimum, maximum) - invalid);
  }
  return answer;
}

const countSubarrays = solve;
class Solution {
  countSubarrays(nums, minK, maxK) { return solve(nums, minK, maxK); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countSubarrays };
