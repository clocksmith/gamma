'use strict';

// 3000. Maximum Area of Longest Diagonal Rectangle (Easy).
// Specification: https://leetcode.com/problems/maximum-area-of-longest-diagonal-rectangle/description/
// O(n) time, O(1) auxiliary space; compare squared diagonals exactly; preserve inputs.
function solve(dimensions) {
  let longestSquared = -1;
  let largestArea = 0;
  for (const [length, width] of dimensions) {
    const diagonalSquared = length * length + width * width;
    const area = length * width;
    if (diagonalSquared > longestSquared || (diagonalSquared === longestSquared && area > largestArea)) {
      longestSquared = diagonalSquared;
      largestArea = area;
    }
  }
  return largestArea;
}

const areaOfMaxDiagonal = solve;
class Solution {
  areaOfMaxDiagonal(dimensions) { return solve(dimensions); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, areaOfMaxDiagonal };
