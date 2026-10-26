'use strict';

// 2461. Maximum Sum of Distinct Subarrays With Length K: maintain the sum and value frequencies of each complete fixed-width window.
// O(n) expected time and O(k) auxiliary space; inputs are read-only.
function solve(nums, k) {
  const counts = new Map();
  let total = 0;
  let best = 0;
  for (let index = 0; index < nums.length; index += 1) {
    const value = nums[index];
    counts.set(value, (counts.get(value) || 0) + 1);
    total += value;
    if (index >= k) {
      const outgoing = nums[index - k];
      total -= outgoing;
      const count = counts.get(outgoing) - 1;
      if (count === 0) counts.delete(outgoing);
      else counts.set(outgoing, count);
    }
    if (index >= k - 1 && counts.size === k) best = Math.max(best, total);
  }
  return best;
}

const maximumSubarraySum = solve;
class Solution {
  maximumSubarraySum(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumSubarraySum };
