'use strict';

// 3350. Adjacent Increasing Subarrays Detection II (Medium).
// Specification: https://leetcode.com/problems/adjacent-increasing-subarrays-detection-ii/description/
function solve(nums) {
  let cnt = 1; let precnt = 0; let ans = 0;
  for (let i = 1; i < nums.length; i++) {
    if (nums[i] > nums[i - 1]) cnt++;
    else { precnt = cnt; cnt = 1; }
    ans = Math.max(ans, Math.min(precnt, cnt), Math.floor(cnt / 2));
  }
  return ans;
}
const maxIncreasingSubarrays = solve;
class Solution { maxIncreasingSubarrays(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxIncreasingSubarrays };
