'use strict';

// 1984. Minimum Difference Between Highest and Lowest of K Scores (Easy).
// Specification: https://leetcode.com/problems/minimum-difference-between-highest-and-lowest-of-k-scores/description/
// O(n log n) time, O(n) space; compare sorted length-k windows without mutating nums.
function solve(nums, k) {
  const values = nums.slice().sort((a, b) => a - b);
  let smallest = values[k - 1] - values[0];
  for (let right = k; right < values.length; right++) {
    smallest = Math.min(smallest, values[right] - values[right - k + 1]);
  }
  return smallest;
}

const minimumDifference = solve;
class Solution {
  minimumDifference(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumDifference };
