'use strict';

// 2274. Maximum Consecutive Floors Without Special Floors: measure gaps between sorted special floors and the two building boundaries.
// O(n log n) time and O(n) auxiliary space; inputs are read-only.
function solve(bottom, top, special) {
  const ordered = special.slice().sort((left, right) => left - right);
  let previous = bottom - 1;
  let best = 0;
  for (const floor of ordered) {
    best = Math.max(best, floor - previous - 1);
    previous = floor;
  }
  return Math.max(best, top - previous);
}

const maxConsecutive = solve;
class Solution {
  maxConsecutive(bottom, top, special) { return solve(bottom, top, special); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxConsecutive };
