'use strict';

// 2248. Intersection of Multiple Arrays (Easy).
// Specification: https://leetcode.com/problems/intersection-of-multiple-arrays/description/
// O(S + U) time, O(U) space; U = 1000. Each input row has distinct values.
function solve(nums) {
  const maximumValue = 1000;
  const counts = new Array(maximumValue + 1).fill(0);
  for (const row of nums) {
    for (const value of row) counts[value]++;
  }
  const result = [];
  for (let value = 1; value <= maximumValue; value++) {
    if (counts[value] === nums.length) result.push(value);
  }
  return result;
}

const intersection = solve;
class Solution {
  intersection(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, intersection };
