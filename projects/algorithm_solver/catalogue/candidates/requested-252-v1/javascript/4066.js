'use strict';

// 4066. Maximum Equal Adjacent Pairs After at Most One Replacement.
// Specification: https://leetcode.com/problems/maximum-equal-adjacent-pairs-after-at-most-one-replacement/description/
// O(n) expected time and O(n) space; count adjacent unordered unequal-value pairs. Inputs are preserved.
function solve(nums) {
  const counts = new Map();
  let equal = 0, gain = 0;
  for (let index = 1; index < nums.length; index++) {
    const left = nums[index - 1], right = nums[index];
    if (left === right) { equal++; continue; }
    const key = Math.min(left, right) + ',' + Math.max(left, right);
    const count = (counts.get(key) || 0) + 1;
    counts.set(key, count);
    gain = Math.max(gain, count);
  }
  return equal + gain;
}

// Native judge method name is not established; canonical solve is the supported entry point.
if (typeof module !== 'undefined') module.exports = { solve };
