'use strict';

// 976. Largest Perimeter Triangle (Easy).
// Specification: https://leetcode.com/problems/largest-perimeter-triangle/description/
// O(n log n) time, O(n) space; the first valid descending triple has maximum perimeter.
function solve(nums) {
  const values = nums.slice().sort((a, b) => b - a);
  for (let index = 0; index + 2 < values.length; index++) {
    if (values[index] < values[index + 1] + values[index + 2]) {
      return values[index] + values[index + 1] + values[index + 2];
    }
  }
  return 0;
}

const largestPerimeter = solve;
class Solution {
  largestPerimeter(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, largestPerimeter };
