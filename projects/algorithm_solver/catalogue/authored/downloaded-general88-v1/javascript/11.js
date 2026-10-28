'use strict';

// 11. Container With Most Water (Medium).
// Specification: https://leetcode.com/problems/container-with-most-water/description/
function solve(height) {
  let left = 0; let right = height.length - 1; let best = 0;
  while (left < right) {
    best = Math.max(best, Math.min(height[left], height[right]) * (right - left));
    if (height[left] < height[right]) left++; else right--;
  }
  return best;
}
const maxArea = solve;
class Solution { maxArea(height) { return solve(height); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxArea };
