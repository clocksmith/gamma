'use strict';

// 2145. Count the Hidden Sequences: intersect the allowed starting values implied by the prefix-sum extremes.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(differences, lower, upper) {
  let current = 0;
  let lowest = 0;
  let highest = 0;
  for (const difference of differences) {
    current += difference;
    lowest = Math.min(lowest, current);
    highest = Math.max(highest, current);
  }
  return Math.max(0, upper - lower - (highest - lowest) + 1);
}

const numberOfArrays = solve;
class Solution {
  numberOfArrays(differences, lower, upper) { return solve(differences, lower, upper); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfArrays };
