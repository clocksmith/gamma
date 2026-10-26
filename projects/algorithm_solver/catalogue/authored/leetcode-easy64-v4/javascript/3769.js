'use strict';

// 3769. Sort Integers by Binary Reflection (Easy).
// Specification: https://leetcode.com/problems/sort-integers-by-binary-reflection/description/
// O(n * (log M + log n)) time, O(n) space; M = max(nums); preserve nums.
function solve(nums) {
  const decorated = [];
  for (const value of nums) {
    let remaining = value;
    let reflection = 0;
    while (remaining > 0) {
      reflection = reflection * 2 + remaining % 2;
      remaining = Math.floor(remaining / 2);
    }
    decorated.push([reflection, value]);
  }
  decorated.sort((left, right) => left[0] - right[0] || left[1] - right[1]);
  return decorated.map(entry => entry[1]);
}

const sortByReflection = solve;
class Solution {
  sortByReflection(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, sortByReflection };
