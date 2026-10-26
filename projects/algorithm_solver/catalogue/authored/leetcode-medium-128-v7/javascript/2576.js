'use strict';

// 2576. Find the Maximum Number of Marked Indices: pair the smallest values with the first sufficiently large values in the upper half.
// O(n log n) time and O(n) auxiliary space; inputs are read-only.
function solve(nums) {
  const ordered = nums.slice().sort((left, right) => left - right);
  let small = 0;
  for (let large = Math.ceil(nums.length / 2); large < nums.length; large += 1) {
    if (2 * ordered[small] <= ordered[large]) small += 1;
  }
  return 2 * small;
}

const maxNumOfMarkedIndices = solve;
class Solution {
  maxNumOfMarkedIndices(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxNumOfMarkedIndices };
