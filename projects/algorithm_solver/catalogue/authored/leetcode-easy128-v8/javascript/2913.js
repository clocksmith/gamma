'use strict';

// 2913. Subarrays Distinct Element Sum of Squares I (Easy).
// Specification: https://leetcode.com/problems/subarrays-distinct-element-sum-of-squares-i/description/
// O(n^2) expected time, O(n) auxiliary space; extend every start while maintaining distinct values.
function solve(nums) {
  let total = 0;
  for (let start = 0; start < nums.length; start++) {
    const distinct = new Set();
    for (let end = start; end < nums.length; end++) {
      distinct.add(nums[end]);
      total += distinct.size * distinct.size;
    }
  }
  return total;
}

const sumCounts = solve;
class Solution {
  sumCounts(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, sumCounts };
