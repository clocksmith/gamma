'use strict';

// Each index enters and leaves each monotone queue once: O(n) time/space.
function solve(nums, limit) {
  const minima = [];
  const maxima = [];
  let minHead = 0;
  let maxHead = 0;
  let left = 0;
  let best = 0;
  for (let right = 0; right < nums.length; right += 1) {
    while (minima.length > minHead && nums[minima[minima.length - 1]] > nums[right]) minima.pop();
    while (maxima.length > maxHead && nums[maxima[maxima.length - 1]] < nums[right]) maxima.pop();
    minima.push(right);
    maxima.push(right);
    while (nums[maxima[maxHead]] - nums[minima[minHead]] > limit) {
      if (minima[minHead] === left) minHead += 1;
      if (maxima[maxHead] === left) maxHead += 1;
      left += 1;
    }
    best = Math.max(best, right - left + 1);
  }
  return best;
}

const longestSubarray = solve;
class Solution {
  longestSubarray(nums, limit) { return solve(nums, limit); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestSubarray };
