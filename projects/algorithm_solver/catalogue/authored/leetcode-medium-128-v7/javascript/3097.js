'use strict';

// 3097. Shortest Subarray With OR at Least K II: maintain per-bit occurrence counts so a sliding-window OR can shrink safely.
// O(30 * n) time and O(30) auxiliary space on the bounded nonnegative integer domain; inputs are read-only.
function solve(nums, k) {
  const counts = new Int32Array(30);
  let current = 0;
  let left = 0;
  let best = nums.length + 1;
  for (let right = 0; right < nums.length; right += 1) {
    const value = nums[right];
    current |= value;
    for (let bit = 0; bit < 30; bit += 1) {
      if ((value & (1 << bit)) !== 0) counts[bit] += 1;
    }
    while (left <= right && current >= k) {
      best = Math.min(best, right - left + 1);
      const removed = nums[left];
      for (let bit = 0; bit < 30; bit += 1) {
        const flag = 1 << bit;
        if ((removed & flag) !== 0) {
          counts[bit] -= 1;
          if (counts[bit] === 0) current ^= flag;
        }
      }
      left += 1;
    }
  }
  return best <= nums.length ? best : -1;
}

const minimumSubarrayLength = solve;
class Solution {
  minimumSubarrayLength(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumSubarrayLength };
