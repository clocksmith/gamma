'use strict';

// 1793. Maximum Score of a Good Subarray.
// Expand from k toward the larger boundary value; O(n) time, O(1) space. Inputs are preserved.

function solve(nums, k) {
  let left = k, right = k, minimum = nums[k], answer = nums[k];
  while (left > 0 || right + 1 < nums.length) {
    if (left === 0 || (right + 1 < nums.length && nums[right + 1] > nums[left - 1])) {
      right += 1; minimum = Math.min(minimum, nums[right]);
    } else { left -= 1; minimum = Math.min(minimum, nums[left]); }
    answer = Math.max(answer, minimum * (right - left + 1));
  }
  return answer;
}

const maximumScore = solve;
class Solution {
  maximumScore(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumScore };
