'use strict';

// 1183. Maximum Number of Ones (Hard).
// Specification: https://leetcode.com/problems/maximum-number-of-ones/description/
function solve(width, height, sideLength, maxOnes) {
  const counts = [];
  for (let i = 0; i < sideLength; i++) {
    let rows = 0;
    for (let r = i; r < height; r += sideLength) rows++;
    for (let j = 0; j < sideLength; j++) {
      let cols = 0;
      for (let c = j; c < width; c += sideLength) cols++;
      counts.push(rows * cols);
    }
  }
  counts.sort((a, b) => b - a);
  let total = 0;
  for (let k = 0; k < maxOnes && k < counts.length; k++) total += counts[k];
  return total;
}
const maximumNumberOfOnes = solve;
class Solution { maximumNumberOfOnes(width, height, sideLength, maxOnes) { return solve(width, height, sideLength, maxOnes); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumNumberOfOnes };
