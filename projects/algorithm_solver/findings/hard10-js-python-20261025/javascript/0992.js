/**
 * 992. Subarrays with K Different Integers (Hard).
 * Fresh candidate authored in this conversation; no repository solution copied.
 * Specification: https://leetcode.com/problems/subarrays-with-k-different-integers/description/
 * Canonical API: solve(nums, k); native alias: subarraysWithKDistinct(nums, k).
 * Inputs are preserved. Gamma independent qualification is pending.
 */
'use strict';

function solve(nums, k) {
  function countAtMost(limit) {
    if (limit <= 0) {
      return 0;
    }
    const frequencies = new Map();
    let left = 0;
    let total = 0;
    for (let right = 0; right < nums.length; right++) {
      const value = nums[right];
      frequencies.set(value, (frequencies.get(value) || 0) + 1);
      while (frequencies.size > limit) {
        const removed = nums[left++];
        const remaining = frequencies.get(removed) - 1;
        if (remaining === 0) {
          frequencies.delete(removed);
        } else {
          frequencies.set(removed, remaining);
        }
      }
      total += right - left + 1;
    }
    return total;
  }
  return countAtMost(k) - countAtMost(k - 1);
}

function subarraysWithKDistinct(nums, k) {
  return solve(nums, k);
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, subarraysWithKDistinct };
}
