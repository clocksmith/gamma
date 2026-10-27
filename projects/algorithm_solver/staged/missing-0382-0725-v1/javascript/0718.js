'use strict';

// 718. Maximum Length of Repeated Subarray.

function solve(nums1, nums2) {
  const dp = Array(nums2.length + 1).fill(0);
  let answer = 0;
  for (const value of nums1) {
    for (let j = nums2.length; j >= 1; j -= 1) {
      dp[j] = value === nums2[j - 1] ? dp[j - 1] + 1 : 0;
      answer = Math.max(answer, dp[j]);
    }
  }
  return answer;
}

const findLength = solve;
class Solution {
  findLength(nums1, nums2) { return solve(nums1, nums2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findLength };
