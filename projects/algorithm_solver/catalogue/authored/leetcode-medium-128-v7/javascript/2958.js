'use strict';

// 2958. Length of Longest Subarray With at Most K Frequency: shrink only until the newly added value meets the frequency limit.
// O(n) expected time and O(n) auxiliary space; inputs are read-only.
function solve(nums, k) {
  const counts = new Map();
  let left = 0;
  let best = 0;
  for (let right = 0; right < nums.length; right += 1) {
    const value = nums[right];
    counts.set(value, (counts.get(value) || 0) + 1);
    while (counts.get(value) > k) {
      const removed = nums[left];
      counts.set(removed, counts.get(removed) - 1);
      left += 1;
    }
    best = Math.max(best, right - left + 1);
  }
  return best;
}

const maxSubarrayLength = solve;
class Solution {
  maxSubarrayLength(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxSubarrayLength };
