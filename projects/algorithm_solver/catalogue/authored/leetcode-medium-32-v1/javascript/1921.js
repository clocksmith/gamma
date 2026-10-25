'use strict';

// 1921. Eliminate Maximum Number of Monsters: shoot in increasing integer deadline order.
// O(n log n) time and O(n) auxiliary space; inputs are read-only.
function solve(dist, speed) {
  const deadlines = dist.map((distance, index) => Math.floor((distance - 1) / speed[index]));
  deadlines.sort((left, right) => left - right);
  for (let minute = 0; minute < deadlines.length; minute += 1) {
    if (deadlines[minute] < minute) return minute;
  }
  return deadlines.length;
}

const eliminateMaximum = solve;
class Solution {
  eliminateMaximum(dist, speed) { return solve(dist, speed); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, eliminateMaximum };
