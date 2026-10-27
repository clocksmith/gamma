'use strict';

// 495. Teemo Attacking.

function solve(timeSeries, duration) {
  if (timeSeries.length === 0) return 0;
  let answer = duration;
  for (let i = 1; i < timeSeries.length; i += 1) answer += Math.min(duration, timeSeries[i] - timeSeries[i - 1]);
  return answer;
}

const findPoisonedDuration = solve;
class Solution {
  findPoisonedDuration(timeSeries, duration) { return solve(timeSeries, duration); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findPoisonedDuration };
