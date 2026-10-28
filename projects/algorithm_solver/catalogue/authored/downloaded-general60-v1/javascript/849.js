'use strict';

// 849. Maximize Distance to Closest Person (Medium).
// Specification: https://leetcode.com/problems/maximize-distance-to-closest-person/description/
function solve(seats) {
  let best = 0; let last = -1;
  for (let i = 0; i < seats.length; i++) {
    if (seats[i] === 1) {
      if (last === -1) best = Math.max(best, i);
      else best = Math.max(best, Math.floor((i - last) / 2));
      last = i;
    }
  }
  best = Math.max(best, seats.length - 1 - last);
  return best;
}
const maxDistToClosest = solve;
class Solution { maxDistToClosest(seats) { return solve(seats); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxDistToClosest };
