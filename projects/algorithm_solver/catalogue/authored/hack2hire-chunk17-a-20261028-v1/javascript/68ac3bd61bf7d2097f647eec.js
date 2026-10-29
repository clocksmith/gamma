"use strict";
// Hack2Hire 68ac3bd61bf7d2097f647eec (Subarray with Most Target Element) over an INFERRED spec; qualification unknown.

function solve(nums, targetIndex, windowSize) {
  const target = nums[targetIndex];
  let count = 0;
  for (let i = 0; i < windowSize; i++) if (nums[i] === target) count++;
  let best = count, start = 0;
  for (let i = 1; i + windowSize <= nums.length; i++) {
    if (nums[i - 1] === target) count--;
    if (nums[i + windowSize - 1] === target) count++;
    if (count > best) { best = count; start = i; }
  }
  return start;
}

function mostTargetWindow(nums, targetIndex, windowSize) { return solve(nums, targetIndex, windowSize); }

module.exports = solve;
module.exports.mostTargetWindow = mostTargetWindow;
