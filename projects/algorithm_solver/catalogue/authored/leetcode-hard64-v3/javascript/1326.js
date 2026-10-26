'use strict';

// 1326. Minimum Number of Taps to Open to Water a Garden: greedy interval coverage; O(n) time and O(n) space. Inputs are preserved.

function solve(n, ranges) {
  const reach = Array(n + 1).fill(0);
  for (let position = 0; position < ranges.length; position += 1) {
    const left = Math.max(0, position - ranges[position]);
    reach[left] = Math.max(reach[left], Math.min(n, position + ranges[position]));
  }
  let taps = 0;
  let boundary = 0;
  let farthest = 0;
  for (let position = 0; position < n; position += 1) {
    farthest = Math.max(farthest, reach[position]);
    if (position === boundary) {
      if (farthest <= position) return -1;
      taps += 1;
      boundary = farthest;
    }
  }
  return taps;
}

const minTaps = solve;
class Solution {
  minTaps(n, ranges) { return solve(n, ranges); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minTaps };
