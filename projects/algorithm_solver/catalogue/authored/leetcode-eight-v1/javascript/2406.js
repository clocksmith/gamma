'use strict';

// O(n log n) time and O(n) space; inputs and nested rows remain unchanged.
function solve(intervals) {
  const starts = intervals.map(row => row[0]).sort((a, b) => a - b);
  const ends = intervals.map(row => row[1]).sort((a, b) => a - b);
  let start = 0;
  let end = 0;
  let active = 0;
  let best = 0;
  while (start < starts.length) {
    // Closed intervals sharing an endpoint must occupy different groups.
    if (starts[start] <= ends[end]) {
      active += 1;
      start += 1;
      best = Math.max(best, active);
    } else {
      active -= 1;
      end += 1;
    }
  }
  return best;
}

const minGroups = solve;
class Solution {
  minGroups(intervals) { return solve(intervals); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minGroups };
