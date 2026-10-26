'use strict';

// 2928. Distribute Candies Among Children I (Easy).
// Specification: https://leetcode.com/problems/distribute-candies-among-children-i/description/
// O(min(n, limit) + 1) time, O(1) space; children are distinct.
function solve(n, limit) {
  let result = 0;
  for (let first = 0; first <= Math.min(n, limit); first++) {
    const remaining = n - first;
    const lowestSecond = Math.max(0, remaining - limit);
    const highestSecond = Math.min(limit, remaining);
    result += Math.max(0, highestSecond - lowestSecond + 1);
  }
  return result;
}

const distributeCandies = solve;
class Solution {
  distributeCandies(n, limit) { return solve(n, limit); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, distributeCandies };
