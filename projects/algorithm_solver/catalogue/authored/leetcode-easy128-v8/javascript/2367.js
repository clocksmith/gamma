'use strict';

// 2367. Number of Arithmetic Triplets (Easy).
// Specification: https://leetcode.com/problems/number-of-arithmetic-triplets/description/
// O(n) expected time, O(n) space; strict increasing order makes value membership sufficient.
function solve(nums, diff) {
  const values = new Set(nums);
  let total = 0;
  for (const value of nums) {
    if (values.has(value + diff) && values.has(value + 2 * diff)) total++;
  }
  return total;
}

const arithmeticTriplets = solve;
class Solution {
  arithmeticTriplets(nums, diff) { return solve(nums, diff); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, arithmeticTriplets };
