'use strict';

// 3028. Ant on the Boundary (Easy).
// Specification: https://leetcode.com/problems/ant-on-the-boundary/description/
// O(n) time, O(1) space; count returns after complete moves, excluding the start.
function solve(nums) {
  let position = 0;
  let result = 0;
  for (const movement of nums) {
    position += movement;
    if (position === 0) result++;
  }
  return result;
}

const returnToBoundaryCount = solve;
class Solution {
  returnToBoundaryCount(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, returnToBoundaryCount };
