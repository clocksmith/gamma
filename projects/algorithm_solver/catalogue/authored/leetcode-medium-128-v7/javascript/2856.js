'use strict';

// 2856. Minimum Array Length After Pair Removals: leave only the unavoidable majority excess or the total-length parity.
// O(n) time and O(1) auxiliary space for the sorted input; inputs are read-only.
function solve(nums) {
  let largest = 0;
  let run = 0;
  let previous;
  for (const value of nums) {
    run = value === previous ? run + 1 : 1;
    largest = Math.max(largest, run);
    previous = value;
  }
  return Math.max(nums.length % 2, 2 * largest - nums.length);
}

const minLengthAfterRemovals = solve;
class Solution {
  minLengthAfterRemovals(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minLengthAfterRemovals };
