'use strict';

// 492. Construct the Rectangle (Easy).
// Specification: https://leetcode.com/problems/construct-the-rectangle/description/
// O(sqrt(area)) time, O(1) auxiliary space; return the closest factor pair, length first.
function solve(area) {
  let width = Math.floor(Math.sqrt(area));
  while (area % width !== 0) width--;
  return [area / width, width];
}

const constructRectangle = solve;
class Solution {
  constructRectangle(area) { return solve(area); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, constructRectangle };
