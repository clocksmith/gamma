'use strict';

// 2294. Partition Array Such That Maximum Difference Is K: start each sorted group with the smallest value not yet covered.
// O(n log n) time and O(n) auxiliary space; inputs are read-only.
function solve(nums, k) {
  const ordered = nums.slice().sort((left, right) => left - right);
  if (ordered.length === 0) return 0;
  let groups = 1;
  let smallest = ordered[0];
  for (const value of ordered) {
    if (value - smallest > k) {
      groups += 1;
      smallest = value;
    }
  }
  return groups;
}

const partitionArray = solve;
class Solution {
  partitionArray(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, partitionArray };
