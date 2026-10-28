'use strict';

// 1696. Jump Game VI (Medium).
// Specification: https://leetcode.com/problems/jump-game-vi/description/
function solve(nums, k) {
  const dp = new Array(nums.length).fill(0);
  dp[0] = nums[0];
  const deque = [0];
  for (let i = 1; i < nums.length; i++) {
    while (deque.length > 0 && deque[0] < i - k) deque.shift();
    dp[i] = nums[i] + dp[deque[0]];
    while (deque.length > 0 && dp[deque[deque.length - 1]] <= dp[i]) deque.pop();
    deque.push(i);
  }
  return dp[nums.length - 1];
}
const maxResult = solve;
class Solution { maxResult(nums, k) { return solve(nums, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxResult };
