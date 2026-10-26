'use strict';

// 3866. First Unique Even Element (Easy).
// Specification: https://leetcode.com/problems/first-unique-even-element/description/
// O(n + 100) time, O(100) space; preserve nums and return the value, not its index.
function solve(nums) {
  const counts = new Array(101).fill(0);
  for (const value of nums) counts[value]++;
  for (const value of nums) {
    if (value % 2 === 0 && counts[value] === 1) return value;
  }
  return -1;
}

const firstUniqueEven = solve;
class Solution {
  firstUniqueEven(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, firstUniqueEven };
