'use strict';

// 3134. Find the Median of the Uniqueness Array.
// Binary search the lower median using counts of windows with at most d distinct values; O(n log n) expected time, O(n) space. Inputs are preserved.

function solve(nums) {
  const n = nums.length, target = Math.floor((n * (n + 1) / 2 + 1) / 2);
  function enough(limit) {
    const counts = new Map();
    let left = 0, total = 0;
    for (let right = 0; right < n; right += 1) {
      counts.set(nums[right], (counts.get(nums[right]) || 0) + 1);
      while (counts.size > limit) {
        const old = nums[left++], count = counts.get(old) - 1;
        if (count === 0) counts.delete(old); else counts.set(old, count);
      }
      total += right - left + 1;
      if (total >= target) return true;
    }
    return false;
  }
  let low = 1, high = new Set(nums).size;
  while (low < high) {
    const middle = Math.floor((low + high) / 2);
    if (enough(middle)) high = middle; else low = middle + 1;
  }
  return low;
}

const medianOfUniquenessArray = solve;
class Solution {
  medianOfUniquenessArray(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, medianOfUniquenessArray };
