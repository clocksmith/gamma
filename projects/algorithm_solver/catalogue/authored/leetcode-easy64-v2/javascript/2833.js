'use strict';

// 2833. Furthest Point From Origin (Easy).
// Specification: https://leetcode.com/problems/furthest-point-from-origin/description/
// O(n) time, O(1) space; direct every underscore toward the larger displacement.
function solve(moves) {
  let displacement = 0;
  let flexible = 0;
  for (const move of moves) {
    if (move === 'L') displacement--;
    else if (move === 'R') displacement++;
    else flexible++;
  }
  return Math.abs(displacement) + flexible;
}

const furthestDistanceFromOrigin = solve;
class Solution {
  furthestDistanceFromOrigin(moves) { return solve(moves); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, furthestDistanceFromOrigin };
