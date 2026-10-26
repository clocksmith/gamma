'use strict';

// 2543. Check if Point Is Reachable. The reachable coordinates have a greatest common divisor that is a power of two; O(log(min(targetX,targetY))) time and O(1) space. Inputs are preserved.

function solve(targetX, targetY) {
  let first = targetX;
  let second = targetY;
  while (second !== 0) [first, second] = [second, first % second];
  return (first & (first - 1)) === 0;
}

const isReachable = solve;
class Solution {
  isReachable(targetX, targetY) { return solve(targetX, targetY); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, isReachable };
