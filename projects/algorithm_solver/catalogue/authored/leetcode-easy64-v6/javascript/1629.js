'use strict';

// 1629. Slowest Key (Easy).
// Specification: https://leetcode.com/problems/slowest-key/description/
// O(n) time, O(1) space; break equal-duration ties by the greatest key; preserve inputs.
function solve(releaseTimes, keysPressed) {
  let previousRelease = 0;
  let longestDuration = -1;
  let slowest = '';
  for (let index = 0; index < releaseTimes.length; index++) {
    const duration = releaseTimes[index] - previousRelease;
    const key = keysPressed[index];
    if (duration > longestDuration || (duration === longestDuration && key > slowest)) {
      longestDuration = duration;
      slowest = key;
    }
    previousRelease = releaseTimes[index];
  }
  return slowest;
}

const slowestKey = solve;
class Solution {
  slowestKey(releaseTimes, keysPressed) { return solve(releaseTimes, keysPressed); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, slowestKey };
