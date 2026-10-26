'use strict';

// 1695. Maximum Erasure Value: maintain a positive-sum window containing distinct values.
// O(n) expected time and O(n) auxiliary space; inputs are read-only.
function solve(nums) {
  const seen = new Set();
  let left = 0;
  let total = 0;
  let best = 0;
  for (const value of nums) {
    while (seen.has(value)) {
      const removed = nums[left];
      seen.delete(removed);
      total -= removed;
      left += 1;
    }
    seen.add(value);
    total += value;
    best = Math.max(best, total);
  }
  return best;
}

const maximumUniqueSubarray = solve;
class Solution {
  maximumUniqueSubarray(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumUniqueSubarray };
