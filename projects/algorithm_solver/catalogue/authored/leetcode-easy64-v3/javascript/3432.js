'use strict';

// 3432. Count Partitions with Even Sum Difference (Easy).
// Specification: https://leetcode.com/problems/count-partitions-with-even-sum-difference/description/
// O(n) time, O(1) space; every partition difference has the parity of the total.
function solve(nums) {
  let total = 0;
  for (const value of nums) total += value;
  return total % 2 === 0 ? nums.length - 1 : 0;
}

const countPartitions = solve;
class Solution {
  countPartitions(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countPartitions };
