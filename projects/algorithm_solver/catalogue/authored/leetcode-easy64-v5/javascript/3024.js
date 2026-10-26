'use strict';

// 3024. Type of Triangle (Easy).
// Specification: https://leetcode.com/problems/type-of-triangle/description/
// O(1) time and space; preserve the three side lengths.
function solve(nums) {
  const [first, second, third] = nums;
  if (first + second <= third || first + third <= second || second + third <= first) return 'none';
  if (first === second && second === third) return 'equilateral';
  if (first === second || first === third || second === third) return 'isosceles';
  return 'scalene';
}

const triangleType = solve;
class Solution {
  triangleType(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, triangleType };
