'use strict';

// 1936. Add Minimum Number of Rungs: fill each consecutive height gap with the minimum number of intermediate rungs.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(rungs, dist) {
  let previous = 0;
  let answer = 0;
  for (const height of rungs) {
    answer += Math.floor((height - previous - 1) / dist);
    previous = height;
  }
  return answer;
}

const addRungs = solve;
class Solution {
  addRungs(rungs, dist) { return solve(rungs, dist); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, addRungs };
