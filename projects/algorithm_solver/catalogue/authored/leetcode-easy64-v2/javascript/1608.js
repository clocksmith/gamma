'use strict';

// 1608. Special Array With X Elements Greater Than or Equal X (Easy).
// Specification: https://leetcode.com/problems/special-array-with-x-elements-greater-than-or-equal-x/description/
// O(n) time, O(n) space; nonnegative values are counted without mutating nums.
function solve(nums) {
  const size = nums.length;
  const counts = new Array(size + 1).fill(0);
  for (const value of nums) counts[Math.min(size, value)]++;
  let atLeast = 0;
  for (let candidate = size; candidate >= 1; candidate--) {
    atLeast += counts[candidate];
    if (atLeast === candidate) return candidate;
  }
  return -1;
}

const specialArray = solve;
class Solution {
  specialArray(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, specialArray };
