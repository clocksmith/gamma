'use strict';

// 832. Flipping an Image (Easy).
// Specification: https://leetcode.com/problems/flipping-an-image/description/
// O(n^2) time and space; reverse each binary row and invert into fresh rows.
function solve(image) {
  return image.map(row => row.slice().reverse().map(value => 1 - value));
}

const flipAndInvertImage = solve;
class Solution {
  flipAndInvertImage(image) { return solve(image); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, flipAndInvertImage };
