'use strict';

// 239. Sliding Window Maximum (Hard).
// Specification: https://leetcode.com/problems/sliding-window-maximum/description/
function solve(nums, k) {
  const deque = [];
  const result = [];
  for (let i = 0; i < nums.length; i++) {
    while (deque.length > 0 && deque[0] <= i - k) deque.shift();
    while (deque.length > 0 && nums[deque[deque.length - 1]] <= nums[i]) deque.pop();
    deque.push(i);
    if (i >= k - 1) result.push(nums[deque[0]]);
  }
  return result;
}
const maxSlidingWindow = solve;
class Solution { maxSlidingWindow(nums, k) { return solve(nums, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxSlidingWindow };
