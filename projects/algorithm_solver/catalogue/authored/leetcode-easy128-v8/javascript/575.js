'use strict';

// 575. Distribute Candies (Easy).
// Specification: https://leetcode.com/problems/distribute-candies/description/
// O(n) expected time, O(n) space; distinct types are capped by the number of candies allowed.
function solve(candyType) {
  return Math.min(new Set(candyType).size, candyType.length / 2);
}

const distributeCandies = solve;
class Solution {
  distributeCandies(candyType) { return solve(candyType); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, distributeCandies };
