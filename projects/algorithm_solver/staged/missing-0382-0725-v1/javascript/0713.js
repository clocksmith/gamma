'use strict';

// 713. Subarray Product Less Than K. Positive-input sliding window; count every valid suffix ending at each position.

function solve(nums, k) {
  if (k <= 1) return 0;
  let left = 0, answer = 0, product = 1;
  for (let right = 0; right < nums.length; right += 1) {
    product *= nums[right];
    while (product >= k) product /= nums[left++];
    answer += right - left + 1;
  }
  return answer;
}

const numSubarrayProductLessThanK = solve;
class Solution {
  numSubarrayProductLessThanK(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numSubarrayProductLessThanK };
