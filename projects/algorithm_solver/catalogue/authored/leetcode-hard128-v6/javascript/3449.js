'use strict';

// 3449. Maximize the Minimum Game Score.
// Binary-search the score and greedily count visits supplied by consecutive edge bounces; O(n log(m*min(points))) time and O(1) space. Inputs are preserved.

function solve(points, m) {
  function possible(score) {
    let moves = 0, carry = 0;
    for (let index = 0; index < points.length; index += 1) {
      const required = Math.ceil(score / points[index]) - carry;
      if (required > 0) { moves += 2 * required - 1; carry = required - 1; }
      else { if (index + 1 < points.length) moves += 1; carry = 0; }
      if (moves > m) return false;
    }
    return true;
  }
  let minimum = Infinity;
  for (const value of points) minimum = Math.min(minimum, value);
  let lower = 0, upper = minimum * m;
  while (lower < upper) {
    const middle = Math.floor((lower + upper + 1) / 2);
    if (possible(middle)) lower = middle; else upper = middle - 1;
  }
  return lower;
}

const maxScore = solve;
class Solution {
  maxScore(points, m) { return solve(points, m); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxScore };
