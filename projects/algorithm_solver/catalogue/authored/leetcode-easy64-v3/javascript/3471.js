'use strict';

// 3471. Find the Largest Almost Missing Integer (Easy).
// Specification: https://leetcode.com/problems/find-the-largest-almost-missing-integer/description/
// O(n * k) expected time, O(n) space; count windows containing each value, not occurrences.
function solve(nums, k) {
  const windows = new Map();
  for (let start = 0; start + k <= nums.length; start++) {
    const present = new Set();
    for (let index = start; index < start + k; index++) present.add(nums[index]);
    for (const value of present) windows.set(value, (windows.get(value) || 0) + 1);
  }
  let largest = -1;
  for (const [value, count] of windows) {
    if (count === 1) largest = Math.max(largest, value);
  }
  return largest;
}

const largestInteger = solve;
class Solution {
  largestInteger(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, largestInteger };
