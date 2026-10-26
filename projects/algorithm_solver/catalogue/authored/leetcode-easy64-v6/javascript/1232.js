'use strict';

// 1232. Check If It Is a Straight Line (Easy).
// Specification: https://leetcode.com/problems/check-if-it-is-a-straight-line/description/
// O(n) time, O(1) space; exact cross products in the public domain; preserve inputs.
function solve(coordinates) {
  const [originX, originY] = coordinates[0];
  const deltaX = coordinates[1][0] - originX;
  const deltaY = coordinates[1][1] - originY;
  for (let index = 2; index < coordinates.length; index++) {
    const [x, y] = coordinates[index];
    if ((x - originX) * deltaY !== (y - originY) * deltaX) return false;
  }
  return true;
}

const checkStraightLine = solve;
class Solution {
  checkStraightLine(coordinates) { return solve(coordinates); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, checkStraightLine };
