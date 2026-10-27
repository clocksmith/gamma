'use strict';

// 3960. Frequency Balance Subarray.
// Specification: https://leetcode.com/problems/frequency-balance-subarray/description/
// O(n^2) expected time and O(n) space; two different frequencies must both occur unless there is one distinct value. Inputs are preserved.
function solve(nums) {
  let answer = 1;
  for (let left = 0; left < nums.length; left++) {
    const counts = new Map();
    const frequencies = new Map();
    for (let right = left; right < nums.length; right++) {
      const value = nums[right];
      const old = counts.get(value) || 0;
      if (old > 0) {
        const remaining = frequencies.get(old) - 1;
        if (remaining === 0) frequencies.delete(old); else frequencies.set(old, remaining);
      }
      counts.set(value, old + 1);
      frequencies.set(old + 1, (frequencies.get(old + 1) || 0) + 1);
      let valid = counts.size === 1;
      if (frequencies.size === 2) {
        const [a, b] = frequencies.keys();
        valid = Math.max(a, b) === 2 * Math.min(a, b);
      }
      if (valid) answer = Math.max(answer, right - left + 1);
    }
  }
  return answer;
}

if (typeof module !== 'undefined') module.exports = { solve };
