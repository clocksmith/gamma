'use strict';

// 1512. Number of Good Pairs (Easy).
// Specification: https://leetcode.com/problems/number-of-good-pairs/description/
function solve(nums) {
  const counts = new Map();
  for (const value of nums) counts.set(value, (counts.get(value) || 0) + 1);
  let total = 0;
  for (const count of counts.values()) total += count * (count - 1) / 2;
  return total;
}
const numIdenticalPairs = solve;
class Solution { numIdenticalPairs(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, numIdenticalPairs };
