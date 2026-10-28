'use strict';

// 1010. Pairs of Songs With Total Durations Divisible by 60 (Medium).
// Specification: https://leetcode.com/problems/pairs-of-songs-with-total-durations-divisible-by-60/description/
function solve(time) {
  const counts = new Array(60).fill(0);
  for (const value of time) counts[value % 60]++;
  let total = 0;
  total += counts[0] * (counts[0] - 1) / 2;
  total += counts[30] * (counts[30] - 1) / 2;
  for (let r = 1; r < 30; r++) total += counts[r] * counts[60 - r];
  return total;
}
const numPairsDivisibleBy60 = solve;
class Solution { numPairsDivisibleBy60(time) { return solve(time); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, numPairsDivisibleBy60 };
