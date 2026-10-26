'use strict';

// 2799. Count Complete Subarrays in an Array: shrink each complete window and count every valid earlier starting position.
// O(n) expected time and O(n) auxiliary space; inputs are read-only.
function solve(nums) {
  const required = new Set(nums).size;
  const counts = new Map();
  let left = 0;
  let result = 0;
  for (const value of nums) {
    counts.set(value, (counts.get(value) || 0) + 1);
    while (counts.size === required) {
      const removed = nums[left];
      const remaining = counts.get(removed) - 1;
      if (remaining === 0) counts.delete(removed);
      else counts.set(removed, remaining);
      left += 1;
    }
    result += left;
  }
  return result;
}

const countCompleteSubarrays = solve;
class Solution {
  countCompleteSubarrays(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countCompleteSubarrays };
