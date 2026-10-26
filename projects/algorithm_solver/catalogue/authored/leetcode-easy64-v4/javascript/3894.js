'use strict';

// 3894. Traffic Signal Color (Easy).
// Specification: https://leetcode.com/problems/traffic-signal-color/description/
// O(1) time and space; use the specified discrete timer conditions, not a periodic cycle.
function solve(timer) {
  if (timer === 0) return 'Green';
  if (timer === 30) return 'Orange';
  if (timer > 30 && timer <= 90) return 'Red';
  return 'Invalid';
}

const trafficSignal = solve;
class Solution {
  trafficSignal(timer) { return solve(timer); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, trafficSignal };
