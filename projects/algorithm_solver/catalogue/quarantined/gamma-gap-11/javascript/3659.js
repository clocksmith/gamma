'use strict';

// 3659. Partition Array Into K-Distinct Groups.
// O(n) expected time and O(n) auxiliary space; inputs are preserved.
function solve(nums, k) {
  if (nums.length % k !== 0) return false;
  const limit = nums.length / k;
  const counts = new Map();
  for (const value of nums) {
    const count = (counts.get(value) || 0) + 1;
    if (count > limit) return false;
    counts.set(value, count);
  }
  return true;
}

const partitionArray = solve;
class Solution {
  partitionArray(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, partitionArray };
