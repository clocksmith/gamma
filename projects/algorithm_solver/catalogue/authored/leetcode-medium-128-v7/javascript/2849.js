'use strict';

// 2849. Determine if a Cell Is Reachable at a Given Time: compare time with Chebyshev distance and handle the one-step return exception.
// O(1) time and O(1) auxiliary space; inputs are read-only.
function solve(sx, sy, fx, fy, t) {
  const distance = Math.max(Math.abs(sx - fx), Math.abs(sy - fy));
  return t >= distance && !(distance === 0 && t === 1);
}

const isReachableAtTime = solve;
class Solution {
  isReachableAtTime(sx, sy, fx, fy, t) { return solve(sx, sy, fx, fy, t); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, isReachableAtTime };
