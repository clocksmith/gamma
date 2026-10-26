'use strict';

// 2537. Count the Number of Good Subarrays: count equal pairs in a window and accumulate all valid left endpoints.
// O(n) expected time and O(n) auxiliary space; inputs are read-only.
function solve(nums, k) {
  const counts = new Map();
  let pairs = 0;
  let left = 0;
  let total = 0;
  for (const value of nums) {
    const count = counts.get(value) || 0;
    pairs += count;
    counts.set(value, count + 1);
    while (pairs >= k) {
      const removed = nums[left];
      const remaining = counts.get(removed) - 1;
      counts.set(removed, remaining);
      pairs -= remaining;
      left += 1;
    }
    total += left;
  }
  return total;
}

const countGood = solve;
class Solution {
  countGood(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countGood };
