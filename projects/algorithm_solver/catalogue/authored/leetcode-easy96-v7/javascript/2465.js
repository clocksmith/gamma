'use strict';

// 2465. Number of Distinct Averages (Easy).
// Specification: https://leetcode.com/problems/number-of-distinct-averages/description/
// O(n log n) time, O(n) space; count distinct extreme-pair sums rather than floating averages; preserve nums.
function solve(nums) {
  const values = nums.slice().sort((a, b) => a - b);
  const sums = new Set();
  for (let index = 0; index < values.length / 2; index++) {
    sums.add(values[index] + values[values.length - 1 - index]);
  }
  return sums.size;
}

const distinctAverages = solve;
class Solution {
  distinctAverages(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, distinctAverages };
