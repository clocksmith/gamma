'use strict';

// 3255. Find the Power of K-Size Subarrays II (Medium).
// Specification: https://leetcode.com/problems/find-the-power-of-k-size-subarrays-ii/description/
function solve(nums, k) {
  const res = [];
  let streak = 0;
  for (let i = 0; i < nums.length; i++) {
    streak = (i > 0 && nums[i] === nums[i - 1] + 1) ? streak + 1 : 1;
    if (i >= k - 1) res.push(streak >= k ? nums[i] : -1);
  }
  return res;
}
const results = solve;
class Solution { results(nums, k) { return solve(nums, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, results };
