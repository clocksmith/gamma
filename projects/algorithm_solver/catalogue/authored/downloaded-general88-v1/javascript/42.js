'use strict';

// 42. Trapping Rain Water (Hard).
// Specification: https://leetcode.com/problems/trapping-rain-water/description/
function solve(height) {
  let left = 0; let right = height.length - 1; let leftMax = 0; let rightMax = 0; let total = 0;
  while (left < right) {
    if (height[left] < height[right]) { if (height[left] >= leftMax) leftMax = height[left]; else total += leftMax - height[left]; left++; }
    else { if (height[right] >= rightMax) rightMax = height[right]; else total += rightMax - height[right]; right--; }
  }
  return total;
}
const trap = solve;
class Solution { trap(height) { return solve(height); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, trap };
