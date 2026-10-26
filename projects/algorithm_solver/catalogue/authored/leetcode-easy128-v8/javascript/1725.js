'use strict';

// 1725. Number Of Rectangles That Can Form The Largest Square (Easy).
// Specification: https://leetcode.com/problems/number-of-rectangles-that-can-form-the-largest-square/description/
// O(n) time, O(1) space; the shorter side bounds the square in each rectangle.
function solve(rectangles) {
  let largest = 0;
  let count = 0;
  for (const [length, width] of rectangles) {
    const side = Math.min(length, width);
    if (side > largest) {
      largest = side;
      count = 1;
    } else if (side === largest) {
      count++;
    }
  }
  return count;
}

const countGoodRectangles = solve;
class Solution {
  countGoodRectangles(rectangles) { return solve(rectangles); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countGoodRectangles };
