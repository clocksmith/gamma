'use strict';

// 2302. Count Subarrays With Score Less Than K. Positive-value sliding window; O(n) time and O(1) auxiliary space. Inputs are preserved.

function solve(nums, k) {
  let left = 0;
  let total = 0;
  let answer = 0;
  for (let right = 0; right < nums.length; right += 1) {
    total += nums[right];
    while (left <= right && total * (right - left + 1) >= k) {
      total -= nums[left];
      left += 1;
    }
    answer += right - left + 1;
  }
  return answer;
}

const countSubarrays = solve;
class Solution {
  countSubarrays(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countSubarrays };
