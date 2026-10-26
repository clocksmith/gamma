'use strict';

// 3194. Minimum Average of Smallest and Largest Elements (Easy).
// Specification: https://leetcode.com/problems/minimum-average-of-smallest-and-largest-elements/description/
// O(n log n) time, O(n) space; preserve nums; half-integer results are exactly representable.
function solve(nums) {
  const ordered = nums.slice().sort((left, right) => left - right);
  let minimumSum = ordered[0] + ordered[ordered.length - 1];
  for (let left = 1; left < ordered.length / 2; left++) {
    minimumSum = Math.min(minimumSum, ordered[left] + ordered[ordered.length - 1 - left]);
  }
  return minimumSum / 2;
}

const minimumAverage = solve;
class Solution {
  minimumAverage(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumAverage };
