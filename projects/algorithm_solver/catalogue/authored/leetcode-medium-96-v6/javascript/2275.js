'use strict';

// 2275. Largest Combination With Bitwise AND Greater Than Zero: count supporters of each bit because a positive AND needs one shared bit.
// O(31n) time and O(1) auxiliary space on the nonnegative 31-bit domain; inputs are read-only.
function solve(candidates) {
  let best = 0;
  for (let bit = 0; bit < 31; bit += 1) {
    const mask = 1 << bit;
    let count = 0;
    for (const value of candidates) if ((value & mask) !== 0) count += 1;
    best = Math.max(best, count);
  }
  return best;
}

const largestCombination = solve;
class Solution {
  largestCombination(candidates) { return solve(candidates); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, largestCombination };
