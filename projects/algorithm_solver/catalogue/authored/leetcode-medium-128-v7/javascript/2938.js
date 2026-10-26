'use strict';

// 2938. Separate Black and White Balls: count each one-before-zero inversion as one required adjacent swap.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(s) {
  let ones = 0;
  let steps = 0;
  for (const character of s) {
    if (character === '1') ones += 1;
    else steps += ones;
  }
  return steps;
}

const minimumSteps = solve;
class Solution {
  minimumSteps(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumSteps };
