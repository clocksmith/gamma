'use strict';

// 2848. Points That Intersect With Cars (Easy).
// Specification: https://leetcode.com/problems/points-that-intersect-with-cars/description/
// O(n + U) time, O(U) space; U = 100. Endpoints are inclusive.
function solve(nums) {
  const maximumPoint = 100;
  const changes = new Array(maximumPoint + 2).fill(0);
  for (const [start, end] of nums) {
    changes[start]++;
    changes[end + 1]--;
  }
  let coverage = 0;
  let result = 0;
  for (let point = 1; point <= maximumPoint; point++) {
    coverage += changes[point];
    if (coverage > 0) result++;
  }
  return result;
}

const numberOfPoints = solve;
class Solution {
  numberOfPoints(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfPoints };
