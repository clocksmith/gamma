/**
 * 42. Trapping Rain Water (Hard).
 * Fresh candidate authored in this conversation; no repository solution copied.
 * Specification: https://leetcode.com/problems/trapping-rain-water/description/
 * Canonical API: solve(height); native alias: trap(height).
 * Inputs are preserved. Gamma independent qualification is pending.
 */
'use strict';

function solve(height) {
  let left = 0;
  let right = height.length - 1;
  let leftMaximum = 0;
  let rightMaximum = 0;
  let water = 0;
  while (left < right) {
    if (height[left] <= height[right]) {
      leftMaximum = Math.max(leftMaximum, height[left]);
      water += leftMaximum - height[left];
      left++;
    } else {
      rightMaximum = Math.max(rightMaximum, height[right]);
      water += rightMaximum - height[right];
      right--;
    }
  }
  return water;
}

function trap(height) {
  return solve(height);
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, trap };
}
