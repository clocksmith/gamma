'use strict';

// 2841. Maximum Sum of Almost Unique Subarray: maintain fixed-window sums and the number of distinct values.
// O(n) expected time and O(k) auxiliary space; inputs are read-only.
function solve(nums, m, k) {
  const counts = new Map();
  let total = 0;
  let best = 0;
  for (let right = 0; right < nums.length; right += 1) {
    const value = nums[right];
    total += value;
    counts.set(value, (counts.get(value) || 0) + 1);
    if (right >= k) {
      const removed = nums[right - k];
      total -= removed;
      const remaining = counts.get(removed) - 1;
      if (remaining === 0) counts.delete(removed);
      else counts.set(removed, remaining);
    }
    if (right + 1 >= k && counts.size >= m) best = Math.max(best, total);
  }
  return best;
}

const maxSum = solve;
class Solution {
  maxSum(nums, m, k) { return solve(nums, m, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxSum };
