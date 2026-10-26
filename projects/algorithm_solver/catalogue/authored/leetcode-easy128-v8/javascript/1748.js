'use strict';

// 1748. Sum of Unique Elements (Easy).
// Specification: https://leetcode.com/problems/sum-of-unique-elements/description/
// O(n) expected time, O(u) space; sum only values whose final frequency is one.
function solve(nums) {
  const counts = new Map();
  for (const value of nums) counts.set(value, (counts.get(value) || 0) + 1);
  let total = 0;
  for (const [value, count] of counts) {
    if (count === 1) total += value;
  }
  return total;
}

const sumOfUnique = solve;
class Solution {
  sumOfUnique(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, sumOfUnique };
