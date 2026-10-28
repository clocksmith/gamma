'use strict';

// 495. Teemo Attacking (Easy).
// Specification: https://leetcode.com/problems/teemo-attacking/description/
function solve(timeSeries, duration) {
  let total = 0;
  for (let i = 0; i < timeSeries.length; i++) {
    if (i === timeSeries.length - 1) total += duration;
    else total += Math.min(duration, timeSeries[i + 1] - timeSeries[i]);
  }
  return total;
}
const findPoisonedDuration = solve;
class Solution { findPoisonedDuration(timeSeries, duration) { return solve(timeSeries, duration); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findPoisonedDuration };
