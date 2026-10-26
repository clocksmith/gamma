'use strict';

// 2161. Partition Array According to Given Pivot: collect the three stable partitions without modifying the original order.
// O(n) time and O(n) auxiliary and result space; inputs are read-only.
function solve(nums, pivot) {
  const smaller = [];
  const equal = [];
  const larger = [];
  for (const value of nums) {
    if (value < pivot) smaller.push(value);
    else if (value === pivot) equal.push(value);
    else larger.push(value);
  }
  return smaller.concat(equal, larger);
}

const pivotArray = solve;
class Solution {
  pivotArray(nums, pivot) { return solve(nums, pivot); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, pivotArray };
