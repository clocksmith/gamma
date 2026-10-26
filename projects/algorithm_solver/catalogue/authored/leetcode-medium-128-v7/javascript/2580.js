'use strict';

// 2580. Count Ways to Group Overlapping Ranges: count connected interval groups and choose either destination for each group.
// O(n log n) time and O(n) auxiliary space; inputs are read-only.
function solve(ranges) {
  const ordered = ranges.slice().sort((left, right) => left[0] - right[0] || left[1] - right[1]);
  const modulus = 1000000007;
  let ways = 1;
  let end = -1;
  for (const [left, right] of ordered) {
    if (left > end) ways = ways * 2 % modulus;
    end = Math.max(end, right);
  }
  return ways;
}

const countWays = solve;
class Solution {
  countWays(ranges) { return solve(ranges); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countWays };
